#!/usr/bin/env python3
"""
Test suite for KW-26 ROMULUS reconstruction.
"""

import unittest
from kw26 import (
    KW26, LFSR,
    text_to_baudot, baudot_to_text,
    majority_combine, generate_cryptovariable
)


class TestBaudot(unittest.TestCase):
    """Test Baudot encoding/decoding."""

    def test_letters(self):
        """Test basic letter encoding."""
        text = "HELLO"
        baudot = text_to_baudot(text)
        result = baudot_to_text(baudot)
        self.assertEqual(result, text)

    def test_with_spaces(self):
        """Test text with spaces."""
        text = "HELLO WORLD"
        baudot = text_to_baudot(text)
        result = baudot_to_text(baudot)
        self.assertEqual(result, text)

    def test_figures(self):
        """Test figure shift."""
        text = "HELLO 123"
        baudot = text_to_baudot(text)
        result = baudot_to_text(baudot)
        self.assertEqual(result, text)

    def test_mixed(self):
        """Test mixed letters and figures."""
        text = "TEST 123 ABC 456"
        baudot = text_to_baudot(text)
        result = baudot_to_text(baudot)
        self.assertEqual(result, text)


class TestLFSR(unittest.TestCase):
    """Test LFSR implementation."""

    def test_lfsr_period(self):
        """Test that LFSR has maximal period."""
        # Small LFSR for testing: x^5 + x^2 + 1 (maximal length)
        lfsr = LFSR(length=5, taps=[0, 2])
        lfsr.load(1)

        # Period should be 2^5 - 1 = 31
        initial = lfsr.state
        count = 0
        while True:
            lfsr.clock()
            count += 1
            if lfsr.state == initial:
                break
            if count > 100:  # Safety limit
                break

        self.assertEqual(count, 31)

    def test_lfsr_deterministic(self):
        """Test that LFSR is deterministic."""
        lfsr1 = LFSR(length=31, taps=[0, 3])
        lfsr2 = LFSR(length=31, taps=[0, 3])

        lfsr1.load(0x12345678)
        lfsr2.load(0x12345678)

        for _ in range(100):
            self.assertEqual(lfsr1.clock(), lfsr2.clock())


class TestCombiner(unittest.TestCase):
    """Test combining function."""

    def test_majority(self):
        """Test majority function truth table."""
        # Majority of (0,0,0) = 0
        self.assertEqual(majority_combine(0, 0, 0) ^ 0, 0)
        # Majority of (1,1,1) = 1, XOR 1 = 0
        self.assertEqual(majority_combine(1, 1, 1), 0)
        # Majority of (1,1,0) = 1, XOR 0 = 1
        self.assertEqual(majority_combine(1, 1, 0), 1)


class TestKW26(unittest.TestCase):
    """Test KW-26 cipher."""

    def test_encrypt_decrypt(self):
        """Test basic encrypt/decrypt cycle."""
        cipher_tx = KW26()
        cipher_rx = KW26()

        plaintext = "SECRET MESSAGE"
        ciphertext = cipher_tx.encrypt(plaintext)
        decrypted = cipher_rx.decrypt(ciphertext)

        self.assertEqual(decrypted.strip(), plaintext.strip())

    def test_different_keys(self):
        """Test that different keys produce different ciphertext."""
        cv1 = generate_cryptovariable()
        cv2 = generate_cryptovariable()

        cipher1 = KW26(cv1)
        cipher2 = KW26(cv2)

        plaintext = "TEST"
        ct1 = cipher1.encrypt(plaintext)
        ct2 = cipher2.encrypt(plaintext)

        # Should be different (with overwhelming probability)
        self.assertNotEqual(ct1, ct2)

    def test_keystream_continuous(self):
        """Test that keystream is continuously generated."""
        cipher = KW26()

        # Generate keystream
        bits1 = [cipher.generate_keystream_bit() for _ in range(50)]
        bits2 = [cipher.generate_keystream_bit() for _ in range(50)]

        # Should be different (continuous, not repeating)
        self.assertNotEqual(bits1, bits2)

    def test_keystream_position(self):
        """Test keystream position tracking."""
        cipher = KW26()

        self.assertEqual(cipher.keystream_position, 0)

        for _ in range(100):
            cipher.generate_keystream_bit()

        self.assertEqual(cipher.keystream_position, 100)

    def test_reset(self):
        """Test cipher reset."""
        cipher = KW26()

        # Generate some keystream
        bits1 = [cipher.generate_keystream_bit() for _ in range(50)]

        # Reset
        cipher.reset()

        # Should get same keystream
        bits2 = [cipher.generate_keystream_bit() for _ in range(50)]

        self.assertEqual(bits1, bits2)


class TestTrafficFlowSecurity(unittest.TestCase):
    """Test traffic flow security property."""

    def test_continuous_stream(self):
        """Verify continuous keystream for traffic flow security."""
        # Status: [KNOWN] - KW-26 provided traffic flow security
        # by transmitting continuous keystream

        cipher = KW26()

        # Should be able to generate unlimited keystream
        for _ in range(10000):
            bit = cipher.generate_keystream_bit()
            self.assertIn(bit, [0, 1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
