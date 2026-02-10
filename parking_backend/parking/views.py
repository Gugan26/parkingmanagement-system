import os
# CRITICAL: This must be set before any other imports to prevent segmentation faults with NumPy 2.x
os.environ["NUMPY_RELAX_UPPER_BOUND"] = "1"

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Reservation, MonthlyPass, YearlyPass, Employee
from .serializers import ReservationSerializer, MonthlyPassSerializer, YearlyPassSerializer, EmployeeSerializer
from .qr import generate_qr
from django.conf import settings
import logging

# Set up logging to track crashes
logger = logging.getLogger(__name__)

import subprocess
import json
import cv2
import numpy as np

@api_view(['POST'])
def verify_face(request):
    temp_path = None
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

        # 4. Attempt Face Verification using Isolated Subprocess (prevents server crash)
        worker_script = os.path.join(os.path.dirname(__file__), 'face_worker.py')
        python_exe = os.path.join(settings.BASE_DIR, 'venv', 'bin', 'python')
        
        try:
            result = subprocess.run(
                [python_exe, worker_script, temp_path, db_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout.strip())
                    if data.get('success'):
                        identity = data.get('identity')
                        filename = os.path.basename(identity)
                        employee = Employee.objects.filter(profile_pic__icontains=filename).first()
                        if employee:
                            return Response({
                                'success': True,
                                'employee': EmployeeSerializer(employee).data
                            })
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse face_worker output: {result.stdout}")
            elif result.returncode == -11 or result.returncode == 139:
                logger.error("Face verification process crashed (Segmentation Fault). Falling back to OpenCV.")
            else:
                logger.error(f"Face verification process failed with code {result.returncode}: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("Face verification process timed out.")
        except Exception as e:
            logger.error(f"Subprocess error: {str(e)}")

        # 5. Fallback to OpenCV (Feature Matching) if DeepFace fails or crashes
        logger.info("Starting OpenCV fallback matching...")
        try:
            best_match = None
            max_matches = 0
            
            # Load probe image
            probe_img = cv2.imread(temp_path, cv2.IMREAD_GRAYSCALE)
            if probe_img is not None:
                orb = cv2.ORB_create()
                kp1, des1 = orb.detectAndCompute(probe_img, None)
                
                if des1 is not None:
                    # Iterate through all employee faces
                    for filename in os.listdir(db_path):
                        if filename.endswith(('.jpg', '.jpeg', '.png')) and not filename.startswith('.'):
                            target_path = os.path.join(db_path, filename)
                            target_img = cv2.imread(target_path, cv2.IMREAD_GRAYSCALE)
                            
                            if target_img is not None:
                                kp2, des2 = orb.detectAndCompute(target_img, None)
                                if des2 is not None:
                                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                                    matches = bf.match(des1, des2)
                                    if len(matches) > max_matches:
                                        max_matches = len(matches)
                                        best_match = filename

            # Threshold for "match" in ORB - 80 is a conservative estimate
            if max_matches > 80:
                employee = Employee.objects.filter(profile_pic__icontains=best_match).first()
                if employee:
                    return Response({
                        'success': True,
                        'employee': EmployeeSerializer(employee).data,
                        'method': 'fallback'
                    })

        except Exception as e:
            logger.error(f"OpenCV fallback error: {str(e)}")

        return Response({'error': 'Face not recognized'}, status=401)

    except Exception as e:
        logger.error(f"Verify Face outer error: {str(e)}")
        return Response({'error': str(e)}, status=500)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except: pass

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
    email = request.data.get('email')
    employee_id = request.data.get('employee_id')
    
    # Check if employee exists to provide better handling or allow update
    existing_employee = Employee.objects.filter(email=email).first() or \
                        Employee.objects.filter(employee_id=employee_id).first()
    
    if existing_employee:
        serializer = EmployeeSerializer(existing_employee, data=request.data, partial=True)
    else:
        serializer = EmployeeSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        status_code = status.HTTP_200_OK if existing_employee else status.HTTP_201_CREATED
        return Response(serializer.data, status=status_code)
    
    print(f"SERIALIZER ERRORS: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)