# qr_generator.py
# Unified QR Code Generator for ArmGuard System
# Standard settings matching JavaScript QRCode library

import qrcode
from pathlib import Path
from PIL import Image
from io import BytesIO


def generate_qr_code(data, output_path=None, size=150):
	"""
	Generate a QR code image from the given data.
	Standard settings matching JavaScript QRCode library:
	- Black & White colors
	- High error correction for reliability
	- Minimal border
	
	Args:
		data (str): The data to encode in the QR code.
		output_path (str or Path, optional): The file path to save the QR code image.
		size (int): The output size in pixels (default: 150).
	
	Returns:
		Path or Image: If output_path provided, returns Path. Otherwise returns PIL Image.
	"""
	# Create QR code with standard settings
	qr = qrcode.QRCode(
		version=1,  # Auto-adjust version
		error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
		box_size=10,  # Size of each box in pixels
		border=1,  # Minimal border (1 box)
	)
	
	qr.add_data(data)
	qr.make(fit=True)
	
	# Create image with black and white colors (matching JavaScript library)
	img = qr.make_image(fill_color="black", back_color="white")
	
	# Resize to specified size
	img = img.resize((size, size), Image.Resampling.LANCZOS)
	
	# Save or return
	if output_path:
		img.save(output_path)
		return Path(output_path)
	else:
		return img


def generate_qr_code_to_buffer(data, size=150):
	"""
	Generate QR code and return as BytesIO buffer (for Django ImageField).
	
	Args:
		data (str): The data to encode in the QR code.
		size (int): The output size in pixels (default: 150).
	
	Returns:
		BytesIO: Buffer containing PNG image data.
	"""
	img = generate_qr_code(data, output_path=None, size=size)
	
	buffer = BytesIO()
	img.save(buffer, format='PNG')
	buffer.seek(0)
	
	return buffer
