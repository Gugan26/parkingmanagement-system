from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Reservation, MonthlyPass, YearlyPass
from .serializers import ReservationSerializer, MonthlyPassSerializer, YearlyPassSerializer, EmployeeSerializer
from .qr import generate_qr
import random
from django.core.mail import send_mail

from django.utils import timezone
from django.conf import settings
import os
from deepface import DeepFace

@api_view(['POST'])
def verify_face(request):
    try:
        # 1. Get uploaded image
        uploaded_file = request.FILES.get('image')
        if not uploaded_file:
            return Response({'error': 'No image provided'}, status=400)

        # 2. Save uploaded image temporarily
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # 3. Ensure DB path exists
        db_path = os.path.join(settings.MEDIA_ROOT, 'employee_faces')
        if not os.path.exists(db_path):
             return Response({'error': 'No registered faces found in database.'}, status=404)

        try:
            # 4. Perform Face Verification (Find match in DB)
            # using VGG-Face model by default, it's good.
            # enforce_detection=False allows processing even if face detection is tricky, but True is safer.
            dfs = DeepFace.find(img_path=temp_path, db_path=db_path, enforce_detection=False, silent=True)
            
            # DeepFace.find returns a list of dataframes
            if len(dfs) > 0 and len(dfs[0]) > 0:
                matched_df = dfs[0]
                # Get the first match
                result_path = matched_df.iloc[0]['identity']
                
                # Extract filename to find employee
                # result_path is absolute, e.g., /media/employee_faces/img.jpg
                filename = os.path.basename(result_path)
                
                # Find Employee
                # We search by profile_pic path ending with this filename
                employee = Employee.objects.filter(profile_pic__icontains=filename).first()
                
                if employee:
                    # Clean up temp
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
                    return Response({
                        'success': True,
                        'employee': EmployeeSerializer(employee).data
                    })

            # Clean up temp
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return Response({'error': 'Face not recognized'}, status=401)

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            # Deepface specific errors
            return Response({'error': f"Verification failed: {str(e)}"}, status=500)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def create_reservation(request):
    serializer = ReservationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_monthly_pass(request):
    serializer = MonthlyPassSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_yearly_pass(request):
    serializer = YearlyPassSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -----------------------------
# CANCEL RESERVATION (Step 1: Generate QR)
# -----------------------------
@api_view(['POST'])
def cancel_reservation(request):
    try:
        spot_id = request.data.get('spot_id')
        email = request.data.get('email', '').lower().strip()
        password = request.data.get('password', '')

        if not spot_id or not email or not password:
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        res_query = Reservation.objects.filter(spot_id=spot_id, email__iexact=email)

        if not res_query.exists():
            return Response({"error": "No reservation found."}, status=status.HTTP_404_NOT_FOUND)

        target_res = res_query.filter(password=password).first()
        if not target_res:
            return Response({"error": "Incorrect password."}, status=status.HTTP_401_UNAUTHORIZED)

        # PASS HOLDER CHECK (No QR needed for them as per your old logic)
        is_monthly = MonthlyPass.objects.filter(email__iexact=email).exists()
        is_yearly = YearlyPass.objects.filter(email__iexact=email).exists()

        if is_yearly or is_monthly:
            target_res.delete() # Pass holders-ku direct delete
            return Response({"success": "Cancelled. Pass holder verified!", "qr": None})

        # NORMAL USER: Generate QR for confirmation
        qr_file_path = generate_qr(spot_id) # qr.py function call
        
        return Response({
            "success": "Please scan the QR code to confirm cancellation.",
            "qr": qr_file_path
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# -----------------------------
# SCANNER ENDPOINT (Step 2: Mobile Scanner hits this)
# -----------------------------
@api_view(['GET']) # POST thevaiyillai
def mark_as_scanned(request, spot_id):
    try:
        # Latest active reservation-ah eduthu is_scanned update panrom
        res = Reservation.objects.filter(spot_id=spot_id, is_scanned=False).last()
        
        if res:
            res.is_scanned = True
            res.save()
            # Mobile-la scan pannavangaluku intha message mattum theriyum
            return Response("<h1>Scan Success! Reservation marked for cancellation.</h1>")
        
        return Response("<h1>Already scanned or No active reservation found.</h1>")
    except Exception as e:
        return Response(f"<h1>Error: {str(e)}</h1>", status=500)
# -----------------------------
# POLLING ENDPOINT (Step 3: Frontend keeps asking this)
# -----------------------------
# views.py
@api_view(['GET'])
def check_scan_status(request, spot_id):
    # active-ah irukura record, mobile-la scan aanatha mattum edukkurom
    res = Reservation.objects.filter(spot_id=spot_id, is_scanned=True).first()
    
    if res:
        # Success message-ah variable-la vechikonga
        data = {"is_scanned": True}
        
        # Database-la irunthu antha record-ah delete pannidunga (Very Important)
        res.delete()
        
        # Ippo Response anupunga
        return Response(data)
    
    return Response({"is_scanned": False})

@api_view(['POST'])
def create_employee(request):
    serializer = EmployeeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)