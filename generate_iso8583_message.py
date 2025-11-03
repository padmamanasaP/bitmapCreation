#!/usr/bin/env python3
"""
ISO 8583 Message Generator for Faster Payment System (FPS)

This script converts JSON field data into a complete ISO 8583 message with:
- Message ID (4 characters)
- Primary bitmap (16 bytes / 32 hex chars)
- Secondary bitmap (16 bytes / 32 hex chars)
- Formatted field data according to field metadata

Field formatting rules:
1. Date fields: Convert from "YYYY-MM-DD HH:MM:SS" to format in value_constraints
2. Numeric fixed-length: Zero-pad to specified length
3. Rate fields: Format as ABBBBBBBBBBB (A=decimal position, B=value without decimal)
4. Subfields: Apply same rules recursively
5. Variable alphanumeric: Length indicator + data (respecting max_length)
6. Fixed alphanumeric: Space-pad to specified length
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import re


class ISO8583MessageGenerator:
    """Generates complete ISO 8583 messages from field data and metadata."""
    
    def __init__(self, message_id="0200"):
        """
        Initialize the message generator.
        
        Args:
            message_id: 4-character message ID (default: "0200")
        """
        if len(message_id) != 4:
            raise ValueError("Message ID must be exactly 4 characters")
        self.message_id = message_id
        self.primary_bitmap = [0] * 64
        self.secondary_bitmap = [0] * 64
        self.field_metadata = {}
        self.formatted_fields = {}
    
    def load_metadata(self, metadata_file):
        """Load field metadata from JSON file."""
        with open(metadata_file, 'r') as f:
            self.field_metadata = json.load(f)
    
    def load_field_data(self, data_file):
        """Load field data values from JSON file."""
        with open(data_file, 'r') as f:
            return json.load(f)
    
    def parse_field_number(self, field_key):
        """Extract field number from field key (e.g., 'f3' -> 3)."""
        if field_key.startswith('f'):
            try:
                return int(field_key[1:])
            except ValueError:
                return None
        return None
    
    def convert_date(self, date_str, output_format):
        """
        Convert date from "YYYY-MM-DD HH:MM:SS" to specified format.
        
        Args:
            date_str: Input date string in format "YYYY-MM-DD HH:MM:SS"
            output_format: Target format (e.g., "MMDDhhmmss", "YYYYMMDD")
        
        Returns:
            Formatted date string
        """
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            
            format_map = {
                'YYYY': '%Y',
                'MM': '%m',
                'DD': '%d',
                'hh': '%H',
                'mm': '%M',
                'ss': '%S'
            }
            
            strftime_format = output_format
            for code, strftime_code in format_map.items():
                strftime_format = strftime_format.replace(code, strftime_code)
            
            return dt.strftime(strftime_format)
        except Exception as e:
            raise ValueError(f"Error converting date '{date_str}' to format '{output_format}': {e}")
    
    def format_numeric_fixed(self, value, length):
        """
        Format numeric value with zero padding.
        
        Args:
            value: Numeric value (string or int)
            length: Target length
        
        Returns:
            Zero-padded string
        """
        value_str = str(value)
        if value_str.startswith('-'):
            sign = '-'
            value_str = value_str[1:]
        else:
            sign = ''
        
        value_str = ''.join(c for c in value_str if c.isdigit())
        
        if len(value_str) > length:
            raise ValueError(f"Numeric value '{value}' exceeds length {length}")
        
        return sign + value_str.zfill(length)
    
    def format_rate(self, value, length):
        """
        Format rate value according to ISO 8583 rate format.
        
        Format: ABBBBBBBBBBB where:
        - A = decimal position from the right (1 digit)
        - B = value without decimal point, zero-padded on left (length-1 digits)
        
        Args:
            value: Rate value (string or float, e.g., "3.45678" or 3.45678)
            length: Total length of formatted output
        
        Returns:
            Formatted rate string
        
        Examples:
            format_rate("3.45678", 12) -> "500000345678"
            format_rate("3", 12) -> "000000000003"
            format_rate(3, 12) -> "000000000003"
        """
        value_str = str(value)
        
        if '.' in value_str:
            parts = value_str.split('.')
            integer_part = parts[0]
            decimal_part = parts[1]
            
            decimal_position = len(decimal_part)
            value_without_decimal = integer_part + decimal_part
            
            value_length = length - 1
            if len(value_without_decimal) > value_length:
                raise ValueError(f"Rate value '{value}' exceeds length {length}")
            
            padded_value = value_without_decimal.zfill(value_length)
            
            return str(decimal_position) + padded_value
        else:
            value_str = ''.join(c for c in value_str if c.isdigit())
            
            if len(value_str) > length:
                raise ValueError(f"Rate value '{value}' exceeds length {length}")
            
            return value_str.zfill(length)
    
    def format_alphanumeric_fixed(self, value, length):
        """
        Format alphanumeric value with space padding.
        
        Args:
            value: Alphanumeric value
            length: Target length
        
        Returns:
            Space-padded string
        """
        value_str = str(value)
        
        if len(value_str) > length:
            raise ValueError(f"Alphanumeric value '{value}' exceeds length {length}")
        
        return value_str.ljust(length)
    
    def format_alphanumeric_variable(self, value, length_indicator_size, max_length):
        """
        Format variable alphanumeric value with length indicator.
        
        Args:
            value: Alphanumeric value
            length_indicator_size: Size of length indicator
            max_length: Maximum allowed length (including indicator)
        
        Returns:
            Length indicator + data
        """
        value_str = str(value)
        data_length = len(value_str)
        
        length_indicator = str(data_length).zfill(length_indicator_size)
        
        total_length = len(length_indicator) + data_length
        if max_length and total_length > max_length:
            raise ValueError(
                f"Total length {total_length} exceeds max_length {max_length} "
                f"for value '{value}'"
            )
        
        return length_indicator + value_str
    
    def format_subfields(self, subfield_values, subfield_metadata):
        """
        Format subfields according to their metadata.
        
        Args:
            subfield_values: Dictionary of subfield tag -> value
            subfield_metadata: List of subfield metadata
        
        Returns:
            Concatenated formatted subfields
        """
        result = ""
        
        for subfield_meta in subfield_metadata:
            tag = subfield_meta['tag']
            
            if tag not in subfield_values:
                if not subfield_meta.get('conditional', False):
                    raise ValueError(f"Required subfield '{tag}' not provided")
                continue
            
            value = subfield_values[tag]
            length = subfield_meta['length']
            format_code = subfield_meta['format']
            
            if format_code.startswith('n'):
                formatted = self.format_numeric_fixed(value, length)
            elif format_code.startswith('ans') or format_code.startswith('an'):
                formatted = self.format_alphanumeric_fixed(value, length)
            else:
                formatted = str(value)[:length].ljust(length)
            
            result += formatted
        
        return result
    
    def format_field(self, field_number, field_value, field_meta):
        """
        Format a single field according to its metadata.
        
        Args:
            field_number: Field number
            field_value: Field value (can be dict for subfields)
            field_meta: Field metadata
        
        Returns:
            Formatted field data
        """
        data_type = field_meta.get('data_type', 'alphanumeric')
        length_type = field_meta.get('length_type', 'fixed')
        length = field_meta.get('length')
        max_length = field_meta.get('max_length')
        length_indicator_size = field_meta.get('length_indicator_size')
        subfields = field_meta.get('subfields', [])
        value_constraints = field_meta.get('value_constraints', '')
        
        if subfields and isinstance(field_value, dict):
            return self.format_subfields(field_value, subfields)
        
        if data_type == 'date':
            format_match = re.search(r'[YMDhms]+', value_constraints)
            if format_match:
                date_format = format_match.group(0)
                return self.convert_date(field_value, date_format)
            else:
                raise ValueError(f"Cannot determine date format from value_constraints: {value_constraints}")
        
        if data_type == 'rate':
            return self.format_rate(field_value, length)
        
        if data_type == 'numeric':
            if length_type == 'fixed':
                return self.format_numeric_fixed(field_value, length)
            else:
                return self.format_alphanumeric_variable(field_value, length_indicator_size, max_length)
        
        if data_type == 'alphanumeric':
            if length_type == 'fixed':
                return self.format_alphanumeric_fixed(field_value, length)
            else:
                return self.format_alphanumeric_variable(field_value, length_indicator_size, max_length)
        
        if data_type == 'hex':
            return str(field_value)
        
        return str(field_value)
    
    def set_field_present(self, field_number):
        """Mark a field as present in the appropriate bitmap."""
        if field_number == 0:
            return
        elif 1 <= field_number <= 64:
            self.primary_bitmap[field_number - 1] = 1
        elif 65 <= field_number <= 128:
            self.secondary_bitmap[field_number - 65] = 1
            self.primary_bitmap[0] = 1
    
    def bitmap_to_hex(self, bitmap):
        """Convert bitmap array to hexadecimal string."""
        hex_string = ""
        for i in range(0, 64, 4):
            nibble = (bitmap[i] << 3) | (bitmap[i+1] << 2) | (bitmap[i+2] << 1) | bitmap[i+3]
            hex_string += format(nibble, 'X')
        return hex_string
    
    def generate_message(self, field_data):
        """
        Generate complete ISO 8583 message.
        
        Args:
            field_data: Dictionary of field_key -> field_value
        
        Returns:
            Complete ISO 8583 message string
        """
        for field_key, field_value in field_data.items():
            field_number = self.parse_field_number(field_key)
            
            if field_number is None or field_number == 0:
                continue
            
            field_meta_key = f"f{field_number}"
            if field_meta_key not in self.field_metadata:
                raise ValueError(f"No metadata found for field {field_number}")
            
            field_meta = self.field_metadata[field_meta_key]
            
            formatted_value = self.format_field(field_number, field_value, field_meta)
            self.formatted_fields[field_number] = formatted_value
            
            self.set_field_present(field_number)
        
        message = self.message_id
        
        primary_hex = self.bitmap_to_hex(self.primary_bitmap)
        secondary_hex = self.bitmap_to_hex(self.secondary_bitmap)
        message += primary_hex + secondary_hex
        
        for field_num in sorted(self.formatted_fields.keys()):
            message += self.formatted_fields[field_num]
        
        return message
    
    def print_message_info(self, message):
        """Print detailed information about the generated message."""
        print(f"Message ID: {self.message_id}")
        print(f"\nPrimary Bitmap: {self.bitmap_to_hex(self.primary_bitmap)}")
        present_fields = [i+1 for i, bit in enumerate(self.primary_bitmap) if bit == 1]
        print(f"  Present fields: {present_fields}")
        
        print(f"\nSecondary Bitmap: {self.bitmap_to_hex(self.secondary_bitmap)}")
        present_fields = [i+65 for i, bit in enumerate(self.secondary_bitmap) if bit == 1]
        print(f"  Present fields: {present_fields}")
        
        print(f"\nFormatted Fields:")
        for field_num in sorted(self.formatted_fields.keys()):
            field_meta_key = f"f{field_num}"
            field_name = self.field_metadata[field_meta_key].get('name', 'Unknown')
            field_value = self.formatted_fields[field_num]
            print(f"  Field {field_num:03d} ({field_name}): {field_value}")
        
        print(f"\nComplete Message:")
        print(f"  {message}")
        print(f"  Length: {len(message)} characters")


def main():
    """Main entry point for the ISO 8583 message generator."""
    parser = argparse.ArgumentParser(
        description='Generate ISO 8583 message from field data and metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python iso8583_message_generator.py -m dataElementsMeta.json -d field_data.json -o message.txt
  
  python iso8583_message_generator.py -m dataElementsMeta.json -d field_data.json -o message.txt --message-id 0210
  
  python iso8583_message_generator.py -m dataElementsMeta.json -d field_data.json -o message.txt -v
        """
    )
    
    parser.add_argument('-m', '--metadata', required=True,
                       help='Field metadata JSON file (dataElementsMeta.json)')
    parser.add_argument('-d', '--data', required=True,
                       help='Field data JSON file with actual values')
    parser.add_argument('-o', '--output', required=True,
                       help='Output message file path')
    parser.add_argument('--message-id', default='0200',
                       help='4-character message ID (default: 0200)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Print detailed message information')
    
    args = parser.parse_args()
    
    if not Path(args.metadata).exists():
        print(f"Error: Metadata file '{args.metadata}' not found", file=sys.stderr)
        sys.exit(1)
    
    if not Path(args.data).exists():
        print(f"Error: Data file '{args.data}' not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        generator = ISO8583MessageGenerator(message_id=args.message_id)
        
        generator.load_metadata(args.metadata)
        field_data = generator.load_field_data(args.data)
        
        message = generator.generate_message(field_data)
        
        with open(args.output, 'w') as f:
            f.write(message)
        
        print(f"✓ ISO 8583 message generated successfully: {args.output}")
        
        if args.verbose:
            print("\nDetailed Message Information:")
            print("=" * 80)
            generator.print_message_info(message)
        else:
            print(f"  Message: {message}")
            print(f"  Length: {len(message)} characters")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
