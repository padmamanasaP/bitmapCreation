#!/usr/bin/env python3
"""
Bitmap Generator for Faster Payment System (FPS)

This script converts JSON metadata about FPS fields into a bitmap file.
The bitmap file format follows ISO 8583 standard:
- First 4 characters: Message ID
- Next 16 bytes (32 hex chars): Primary bitmap (fields 1-64)
- Next 16 bytes (32 hex chars): Secondary bitmap (fields 65-128)

The bitmap indicates which fields are present in the message.
"""

import json
import sys
import argparse
from pathlib import Path


class BitmapGenerator:
    """Generates bitmap files from JSON field metadata."""
    
    def __init__(self, message_id="0200"):
        """
        Initialize the bitmap generator.
        
        Args:
            message_id: 4-character message ID (default: "0200")
        """
        if len(message_id) != 4:
            raise ValueError("Message ID must be exactly 4 characters")
        self.message_id = message_id
        self.primary_bitmap = [0] * 64  # Bits for fields 1-64
        self.secondary_bitmap = [0] * 64  # Bits for fields 65-128
    
    def load_json_metadata(self, json_file_path):
        """
        Load field metadata from JSON file.
        
        Args:
            json_file_path: Path to the JSON file containing field metadata
            
        Returns:
            Dictionary of field metadata
        """
        with open(json_file_path, 'r') as f:
            return json.load(f)
    
    def parse_field_number(self, field_key):
        """
        Extract field number from field key (e.g., 'f3' -> 3).
        
        Args:
            field_key: Field key from JSON (e.g., 'f0', 'f1', 'f3')
            
        Returns:
            Integer field number or None if invalid
        """
        if field_key.startswith('f'):
            try:
                return int(field_key[1:])
            except ValueError:
                return None
        return None
    
    def set_field_present(self, field_number):
        """
        Mark a field as present in the appropriate bitmap.
        
        Args:
            field_number: Field number (0-128)
        """
        if field_number == 0:
            return
        elif 1 <= field_number <= 64:
            self.primary_bitmap[field_number - 1] = 1
        elif 65 <= field_number <= 128:
            self.secondary_bitmap[field_number - 65] = 1
            self.primary_bitmap[0] = 1
    
    def bitmap_to_hex(self, bitmap):
        """
        Convert bitmap array to hexadecimal string.
        
        Args:
            bitmap: List of 64 bits (0 or 1)
            
        Returns:
            32-character hexadecimal string (16 bytes)
        """
        hex_string = ""
        for i in range(0, 64, 4):
            nibble = (bitmap[i] << 3) | (bitmap[i+1] << 2) | (bitmap[i+2] << 1) | bitmap[i+3]
            hex_string += format(nibble, 'X')
        return hex_string
    
    def generate_bitmap_from_json(self, json_file_path, fields_to_include=None):
        """
        Generate bitmap based on fields present in JSON metadata.
        
        Args:
            json_file_path: Path to JSON file with field metadata
            fields_to_include: Optional list of field numbers to include.
                             If None, all fields in JSON are included.
        """
        metadata = self.load_json_metadata(json_file_path)
        
        for field_key, field_data in metadata.items():
            field_number = self.parse_field_number(field_key)
            
            if field_number is None:
                continue
            
            if fields_to_include is not None:
                if field_number not in fields_to_include:
                    continue
            
            self.set_field_present(field_number)
    
    def generate_bitmap_file(self, output_path):
        """
        Generate the complete bitmap file.
        
        Args:
            output_path: Path where the bitmap file will be written
            
        Returns:
            The bitmap content as a string
        """
        primary_hex = self.bitmap_to_hex(self.primary_bitmap)
        secondary_hex = self.bitmap_to_hex(self.secondary_bitmap)
        
        bitmap_content = self.message_id + primary_hex + secondary_hex
        
        with open(output_path, 'w') as f:
            f.write(bitmap_content)
        
        return bitmap_content
    
    def print_bitmap_info(self):
        """Print detailed information about the bitmap."""
        print(f"Message ID: {self.message_id}")
        print(f"\nPrimary Bitmap (Fields 1-64):")
        print(f"  Binary: {''.join(map(str, self.primary_bitmap))}")
        print(f"  Hex: {self.bitmap_to_hex(self.primary_bitmap)}")
        
        present_fields = [i+1 for i, bit in enumerate(self.primary_bitmap) if bit == 1]
        print(f"  Present fields: {present_fields}")
        
        print(f"\nSecondary Bitmap (Fields 65-128):")
        print(f"  Binary: {''.join(map(str, self.secondary_bitmap))}")
        print(f"  Hex: {self.bitmap_to_hex(self.secondary_bitmap)}")
        
        present_fields = [i+65 for i, bit in enumerate(self.secondary_bitmap) if bit == 1]
        print(f"  Present fields: {present_fields}")


def main():
    """Main entry point for the bitmap generator."""
    parser = argparse.ArgumentParser(
        description='Generate bitmap file from JSON field metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt
  
  python bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt -m 0210
  
  python bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt -f 3,4,6,7,11,12
  
  python bitmap_generator.py -i dataElementsMeta.json -o bitmap.txt -v
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                       help='Input JSON file with field metadata')
    parser.add_argument('-o', '--output', required=True,
                       help='Output bitmap file path')
    parser.add_argument('-m', '--message-id', default='0200',
                       help='4-character message ID (default: 0200)')
    parser.add_argument('-f', '--fields',
                       help='Comma-separated list of field numbers to include (e.g., 3,4,6,7)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Print detailed bitmap information')
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    fields_to_include = None
    if args.fields:
        try:
            fields_to_include = [int(f.strip()) for f in args.fields.split(',')]
        except ValueError:
            print("Error: Invalid field numbers. Use comma-separated integers.", file=sys.stderr)
            sys.exit(1)
    
    try:
        generator = BitmapGenerator(message_id=args.message_id)
        
        generator.generate_bitmap_from_json(args.input, fields_to_include)
        
        bitmap_content = generator.generate_bitmap_file(args.output)
        
        print(f"✓ Bitmap file generated successfully: {args.output}")
        print(f"  Content: {bitmap_content}")
        print(f"  Length: {len(bitmap_content)} characters")
        
        if args.verbose:
            print("\nDetailed Bitmap Information:")
            print("=" * 60)
            generator.print_bitmap_info()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
