#!/usr/bin/env python3
"""
KW-26 ROMULUS - A Plausible Reconstruction
==========================================

A historically-informed reconstruction of the TSEC/KW-26 ROMULUS
teleprinter cipher, based on declassified documentation and known
principles of 1950s-era LFSR stream ciphers.

THIS IS NOT THE ACTUAL KW-26 ALGORITHM.
See DEVIATIONS.md for detailed documentation of all design choices.

Author: Zane Hambly, 2025
License: MIT
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import struct


# =============================================================================
# BAUDOT / ITA2 ENCODING
# Status: [KNOWN] - Standard teleprinter encoding
# =============================================================================

# ITA2 (International Telegraph Alphabet No. 2) - Baudot code
# Two "shifts": LETTERS and FIGURES
LTRS_SHIFT = 0x1F  # Shift to letters
FIGS_SHIFT = 0x1B  # Shift to figures

BAUDOT_LTRS = {
    'A': 0x03, 'B': 0x19, 'C': 0x0E, 'D': 0x09, 'E': 0x01,
    'F': 0x0D, 'G': 0x1A, 'H': 0x14, 'I': 0x06, 'J': 0x0B,
    'K': 0x0F, 'L': 0x12, 'M': 0x1C, 'N': 0x0C, 'O': 0x18,
    'P': 0x16, 'Q': 0x17, 'R': 0x0A, 'S': 0x05, 'T': 0x10,
    'U': 0x07, 'V': 0x1E, 'W': 0x13, 'X': 0x1D, 'Y': 0x15,
    'Z': 0x11, ' ': 0x04, '\r': 0x08, '\n': 0x02,
}

BAUDOT_FIGS = {
    '1': 0x17, '2': 0x13, '3': 0x01, '4': 0x0A, '5': 0x10,
    '6': 0x15, '7': 0x07, '8': 0x06, '9': 0x18, '0': 0x16,
    '-': 0x03, '?': 0x19, ':': 0x0E, '$': 0x09, '!': 0x0D,
    '&': 0x1A, '#': 0x14, "'": 0x0B, '(': 0x0F, ')': 0x12,
    '.': 0x1C, ',': 0x0C, ';': 0x1E, '/': 0x1D, '"': 0x11,
    ' ': 0x04, '\r': 0x08, '\n': 0x02,
}

# Reverse mappings
LTRS_DECODE = {v: k for k, v in BAUDOT_LTRS.items()}
FIGS_DECODE = {v: k for k, v in BAUDOT_FIGS.items()}


def text_to_baudot(text: str) -> List[int]:
    """
    Convert ASCII text to Baudot/ITA2 codes.

    Status: [KNOWN] - Standard teleprinter encoding
    """
    result = []
    in_figures = False

    for char in text.upper():
        if char in BAUDOT_LTRS:
            if in_figures:
                result.append(LTRS_SHIFT)
                in_figures = False
            result.append(BAUDOT_LTRS[char])
        elif char in BAUDOT_FIGS:
            if not in_figures:
                result.append(FIGS_SHIFT)
                in_figures = True
            result.append(BAUDOT_FIGS[char])
        # Unknown characters silently dropped

    return result


def baudot_to_text(codes: List[int]) -> str:
    """
    Convert Baudot/ITA2 codes to ASCII text.

    Status: [KNOWN] - Standard teleprinter encoding
    """
    result = []
    in_figures = False

    for code in codes:
        if code == LTRS_SHIFT:
            in_figures = False
        elif code == FIGS_SHIFT:
            in_figures = True
        elif code == 0x00:
            pass  # NULL - ignore
        else:
            if in_figures and code in FIGS_DECODE:
                result.append(FIGS_DECODE[code])
            elif code in LTRS_DECODE:
                result.append(LTRS_DECODE[code])

    return ''.join(result)


# =============================================================================
# LINEAR FEEDBACK SHIFT REGISTER (LFSR)
# Status: [KNOWN] that LFSRs were used
#         [RECONSTRUCTED] specific configuration
# =============================================================================

@dataclass
class LFSR:
    """
    A single Linear Feedback Shift Register.

    The feedback polynomial determines which bits are XORed to produce
    the new input bit. We represent taps as a list of bit positions.

    Status: [KNOWN] - LFSR principle
            [RECONSTRUCTED] - Specific polynomials
    """
    length: int
    taps: List[int]  # Bit positions for feedback (0-indexed from right)
    state: int = 0   # Current register state

    def __post_init__(self):
        # Mask for register length
        self.mask = (1 << self.length) - 1

    def clock(self) -> int:
        """
        Clock the register once, return output bit.

        The output bit is the rightmost bit.
        The feedback bit is XOR of all tap positions.
        """
        # Output bit (rightmost)
        output = self.state & 1

        # Calculate feedback bit (XOR of taps)
        feedback = 0
        for tap in self.taps:
            feedback ^= (self.state >> tap) & 1

        # Shift right, insert feedback at left
        self.state = ((self.state >> 1) | (feedback << (self.length - 1))) & self.mask

        return output

    def load(self, initial_state: int):
        """Load initial state (from cryptovariable)."""
        self.state = initial_state & self.mask
        # Ensure non-zero state (all-zeros locks LFSR)
        if self.state == 0:
            self.state = 1


# =============================================================================
# COMBINING FUNCTION
# Status: [RECONSTRUCTED] - Nonlinearity required but specific function unknown
# =============================================================================

def majority_combine(a: int, b: int, c: int) -> int:
    """
    Nonlinear combining function using majority + XOR.

    Status: [RECONSTRUCTED]

    Rationale: Majority function was known in 1950s, provides
    correlation immunity, simple to implement with vacuum tubes.

    See DEVIATIONS.md section 2.1 for full rationale.
    """
    # Majority: output 1 if 2 or more inputs are 1
    majority = (a & b) | (b & c) | (a & c)
    # XOR with third input for additional nonlinearity
    return majority ^ c


# =============================================================================
# KW-26 CIPHER
# =============================================================================

# LFSR configurations
# Status: [RECONSTRUCTED] - Lengths and polynomials are speculative
# See DEVIATIONS.md sections 1.2 and 1.3

LFSR_CONFIGS = [
    # (length, taps) - taps are positions that feed back
    # Polynomial x^31 + x^3 + 1 -> taps at positions 0 and 3
    (31, [0, 3]),
    # Polynomial x^29 + x^2 + 1 -> taps at positions 0 and 2
    (29, [0, 2]),
    # Polynomial x^23 + x^5 + 1 -> taps at positions 0 and 5
    (23, [0, 5]),
]


class KW26:
    """
    KW-26 ROMULUS Cipher - Plausible Reconstruction

    A stream cipher using multiple LFSRs with a nonlinear combining
    function, XORed with 5-bit Baudot teleprinter codes.

    Status: [KNOWN] - Overall architecture (LFSR + Baudot XOR)
            [RECONSTRUCTED] - Specific implementation details
    """

    def __init__(self, cryptovariable: bytes = None):
        """
        Initialize the KW-26 cipher.

        Args:
            cryptovariable: The daily key, loaded from punch card.
                           If None, uses a default test key.
        """
        # Create LFSRs
        # Status: [RECONSTRUCTED] - Three LFSRs with nonlinear combining
        self.lfsrs = [
            LFSR(length=cfg[0], taps=cfg[1])
            for cfg in LFSR_CONFIGS
        ]

        # Track keystream position for debugging
        self.keystream_position = 0

        # Load cryptovariable or default
        if cryptovariable is None:
            # Default test key - NOT FOR OPERATIONAL USE
            self._load_test_key()
        else:
            self._load_cryptovariable(cryptovariable)

    def _load_test_key(self):
        """
        Load a default test key for development.

        Status: [RECONSTRUCTED] - Test vector, not historical
        """
        # Simple test initialization
        self.lfsrs[0].load(0x5A5A5A5A)  # 31-bit
        self.lfsrs[1].load(0x12345678)  # 29-bit
        self.lfsrs[2].load(0x00ABCDEF)  # 23-bit

    def _load_cryptovariable(self, cv: bytes):
        """
        Load cryptovariable from punch card data.

        Status: [RECONSTRUCTED] - Key loading mechanism is speculative

        The actual KW-26 used 45-column Remington Rand punch cards.
        This reconstruction assumes direct bit mapping.

        See DEVIATIONS.md section 3 for rationale.

        Args:
            cv: At least 11 bytes (88 bits) for the three LFSRs
        """
        if len(cv) < 11:
            raise ValueError("Cryptovariable must be at least 11 bytes")

        # Extract LFSR initial states
        # LFSR-A: 31 bits from bytes 0-3 (use low 31 bits)
        state_a = struct.unpack('>I', cv[0:4])[0] & 0x7FFFFFFF

        # LFSR-B: 29 bits from bytes 4-7 (use low 29 bits)
        state_b = struct.unpack('>I', cv[4:8])[0] & 0x1FFFFFFF

        # LFSR-C: 23 bits from bytes 8-10 (use low 23 bits)
        state_c = (cv[8] << 16) | (cv[9] << 8) | cv[10]
        state_c &= 0x7FFFFF

        self.lfsrs[0].load(state_a)
        self.lfsrs[1].load(state_b)
        self.lfsrs[2].load(state_c)

    def generate_keystream_bit(self) -> int:
        """
        Generate one bit of keystream.

        Status: [KNOWN] - Continuous keystream generation
                [RECONSTRUCTED] - Specific combining function

        Returns:
            Single keystream bit (0 or 1)
        """
        # Clock all LFSRs and get output bits
        bits = [lfsr.clock() for lfsr in self.lfsrs]

        # Combine nonlinearly
        # Status: [RECONSTRUCTED] - See DEVIATIONS.md section 2.1
        output = majority_combine(bits[0], bits[1], bits[2])

        self.keystream_position += 1
        return output

    def generate_keystream_byte(self) -> int:
        """Generate 8 bits of keystream as a byte."""
        byte = 0
        for i in range(8):
            byte = (byte << 1) | self.generate_keystream_bit()
        return byte

    def encrypt_baudot(self, plaintext_codes: List[int]) -> List[int]:
        """
        Encrypt Baudot codes.

        Status: [KNOWN] - XOR with keystream

        Args:
            plaintext_codes: List of 5-bit Baudot codes

        Returns:
            List of encrypted 5-bit codes
        """
        ciphertext = []
        for code in plaintext_codes:
            # Generate 5 keystream bits
            key_bits = 0
            for _ in range(5):
                key_bits = (key_bits << 1) | self.generate_keystream_bit()

            # XOR plaintext with keystream
            # Status: [KNOWN] - Explicitly documented
            encrypted = code ^ key_bits
            ciphertext.append(encrypted)

        return ciphertext

    def decrypt_baudot(self, ciphertext_codes: List[int]) -> List[int]:
        """
        Decrypt Baudot codes.

        Decryption is identical to encryption (XOR is self-inverse).

        Status: [KNOWN] - XOR is symmetric
        """
        # XOR is its own inverse
        return self.encrypt_baudot(ciphertext_codes)

    def encrypt(self, plaintext: str) -> List[int]:
        """
        Encrypt ASCII text to encrypted Baudot codes.

        Args:
            plaintext: ASCII text to encrypt

        Returns:
            List of encrypted 5-bit Baudot codes
        """
        baudot = text_to_baudot(plaintext)
        return self.encrypt_baudot(baudot)

    def decrypt(self, ciphertext: List[int]) -> str:
        """
        Decrypt Baudot codes to ASCII text.

        Args:
            ciphertext: List of encrypted 5-bit Baudot codes

        Returns:
            Decrypted ASCII text
        """
        baudot = self.decrypt_baudot(ciphertext)
        return baudot_to_text(baudot)

    def reset(self, cryptovariable: bytes = None):
        """Reset the cipher to initial state."""
        self.keystream_position = 0
        if cryptovariable:
            self._load_cryptovariable(cryptovariable)
        else:
            self._load_test_key()

    def get_state(self) -> dict:
        """Return current cipher state for debugging."""
        return {
            'position': self.keystream_position,
            'lfsr_states': [lfsr.state for lfsr in self.lfsrs],
        }


# =============================================================================
# CRYPTOVARIABLE (KEY) MANAGEMENT
# =============================================================================

def generate_cryptovariable() -> bytes:
    """
    Generate a random cryptovariable (for testing).

    Status: [RECONSTRUCTED] - Format is speculative

    In the real KW-26, cryptovariables were distributed on
    punch cards and physically destroyed after use.
    """
    import os
    return os.urandom(16)  # 128 bits - more than needed


def load_cryptovariable_from_card(card_data: bytes) -> bytes:
    """
    Parse a simulated punch card into cryptovariable.

    Status: [RECONSTRUCTED] - Card format is speculative

    The real KW-26 used 45-column Remington Rand (UNIVAC) format
    punch cards with round holes.

    This simulation assumes a simple binary format.
    """
    # For now, just return the raw bytes
    # A more sophisticated simulation would parse column data
    return card_data


# =============================================================================
# DEMONSTRATION
# =============================================================================

def demo():
    """Demonstrate the KW-26 reconstruction."""

    print("""
+==================================================================+
|            KW-26 ROMULUS - Plausible Reconstruction              |
|                                                                  |
|  THIS IS NOT THE ACTUAL KW-26 ALGORITHM                          |
|  See DEVIATIONS.md for reconstruction rationale                  |
|                                                                  |
|  Based on:                                                       |
|    - NSA declassified publications                               |
|    - Known 1950s LFSR stream cipher principles                   |
|    - Hardware constraints (~800 cores, vacuum tubes)             |
+==================================================================+
    """)

    # Create cipher with test key
    cipher_tx = KW26()
    cipher_rx = KW26()  # Same key = same keystream

    # Test message
    plaintext = "HELLO WORLD"

    print(f"Plaintext:  {plaintext}")
    print(f"Baudot:     {text_to_baudot(plaintext)}")

    # Encrypt
    ciphertext = cipher_tx.encrypt(plaintext)
    print(f"Ciphertext: {ciphertext}")

    # Decrypt (with fresh cipher at same initial state)
    decrypted = cipher_rx.decrypt(ciphertext)
    print(f"Decrypted:  {decrypted}")

    # Verify
    assert decrypted.strip() == plaintext.strip(), "Decryption failed!"
    print("\n[OK] Encryption/decryption verified")

    # Show keystream characteristics
    print("\n--- Keystream Analysis ---")
    cipher = KW26()

    # Generate some keystream
    keystream = [cipher.generate_keystream_bit() for _ in range(100)]
    ones = sum(keystream)
    print(f"First 100 bits: {ones} ones, {100-ones} zeros")
    print(f"Bits: {''.join(str(b) for b in keystream[:50])}...")

    print("\n--- LFSR States ---")
    state = cipher.get_state()
    for i, s in enumerate(state['lfsr_states']):
        print(f"LFSR-{chr(65+i)}: 0x{s:08X}")

    print(f"\nKeystream position: {state['position']} bits generated")

    print("\n" + "=" * 60)
    print("Reconstruction complete. See DEVIATIONS.md for details.")
    print("=" * 60)


if __name__ == "__main__":
    demo()
