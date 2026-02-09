from django.db import models

class Reservation(models.Model):
    SPOT_TYPE = (
        ('car', 'Car'),
        ('bike', 'Bike'),
    )

    spot_id = models.CharField(max_length=20)
    spot_type = models.CharField(max_length=10, choices=SPOT_TYPE)

    name = models.CharField(max_length=100)
    email = models.EmailField()

    password = models.CharField(max_length=100, default="")

    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.FloatField()
    is_scanned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.spot_id} - {self.name}"


class MonthlyPass(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    age = models.IntegerField()
    vehicle_number = models.CharField(max_length=20)

    start_time = models.TimeField()
    end_time = models.TimeField()

    start_date = models.DateField()
    end_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Monthly - {self.vehicle_number}"


class YearlyPass(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    age = models.IntegerField()
    vehicle_number = models.CharField(max_length=20)

    start_time = models.TimeField()
    end_time = models.TimeField()

    start_date = models.DateField()
    end_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Yearly - {self.vehicle_number}"
    

class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    employee_id = models.CharField(max_length=20, unique=True)
    age = models.IntegerField()
    vehicle_number = models.CharField(max_length=20)
    profile_pic = models.ImageField(upload_to='employee_faces/', blank=True, null=True)

    def __str__(self):
        return self.name

