from print_handler.pdf_filler import qr_print_layout

config = qr_print_layout.get_layout_config()

print('=== QR Print Layout Configuration ===')
print(f'Paper Size: {qr_print_layout.PAPER_SIZE_NAME}')
print(f'Card Size: {qr_print_layout.CARD_WIDTH_MM}mm x {qr_print_layout.CARD_HEIGHT_MM}mm')
print(f'QR Size: {qr_print_layout.QR_SIZE_MM}mm')
print(f'Cards Per Row: {qr_print_layout.CARDS_PER_ROW}')
print(f'Gap: H={qr_print_layout.HORIZONTAL_GAP_MM}mm, V={qr_print_layout.VERTICAL_GAP_MM}mm')
print(f'\nCalculated rows per page: {config["rows_per_page"]}')
print('\n✓ Configuration loaded successfully!')
print('\nTo adjust these settings, edit:')
print('  armguard/print_handler/pdf_filler/qr_print_layout.py')
