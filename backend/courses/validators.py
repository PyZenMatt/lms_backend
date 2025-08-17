import os
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

def validate_video_file(file):
    """
    Validator per file video che controlla:
    - Tipo di file
    - Dimensione massima (200MB)
    - Estensioni permesse
    """
    if not isinstance(file, UploadedFile):
        return
    
    # Check file size (200MB max)
    max_size = 200 * 1024 * 1024  # 200MB in bytes
    if file.size > max_size:
        raise ValidationError(f'Il file video è troppo grande. Massimo {max_size // (1024*1024)}MB permessi.')
    
    # Check file extension
    valid_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension not in valid_extensions:
        raise ValidationError(f'Formato file non supportato. Estensioni permesse: {", ".join(valid_extensions)}')
    
    # Check MIME type
    valid_mime_types = [
        'video/mp4',
        'video/avi',
        'video/quicktime',
        'video/x-msvideo',
        'video/x-flv',
        'video/webm',
        'video/x-matroska'
    ]
    
    if hasattr(file, 'content_type') and file.content_type:
        if not any(file.content_type.startswith(mime) for mime in valid_mime_types):
            raise ValidationError(f'Tipo MIME non supportato: {file.content_type}')
