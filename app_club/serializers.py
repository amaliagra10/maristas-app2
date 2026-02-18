# serializers.py
from rest_framework import serializers 

class PresencialidadEntrenadorSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lon = serializers.DecimalField(max_digits=9, decimal_places=6)

