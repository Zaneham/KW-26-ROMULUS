# KW-26 ROMULUS - A Plausible Reconstruction

**A historically-informed reconstruction of the TSEC/KW-26 ROMULUS teleprinter cipher.**

*For when you want to encrypt your telegrams like it's 1956 but can't be bothered getting a security clearance.*

## Important Disclaimer

**This is NOT the actual KW-26 algorithm.**

The specific shift register configuration, feedback polynomial, and combining functions used in the real TSEC/KW-26 remain classified by the National Security Agency. 

This implementation is a *plausible reconstruction* based on:

1. Declassified operational documentation
2. Known principles of 1950s-era LFSR stream ciphers
3. Physical constraints implied by the hardware (800+ magnetic cores, vacuum tube logic)
4. Contemporary academic literature on shift register cryptography

Every design decision is documented with its source: `[KNOWN]` for declassified facts, `[RECONSTRUCTED]` for educated engineering choices.

## What We Know For Certain

Things the NSA has graciously allowed us to know, presumably because knowing them no longer matters, or perhaps because someone left a filing cabinet unlocked in 1987.

| Fact | Source | Classification |
|------|--------|----------------|
| LFSR-based stream cipher | NSA publications | `[KNOWN]` |
| XOR with 5-bit Baudot code | NSA publications | `[KNOWN]` |
| Continuous keystream (traffic flow security) | NSA publications | `[KNOWN]` |
| Cryptovariable loaded from 45-column punch card | NSA publications | `[KNOWN]` |
| ~800 magnetic cores | Operator accounts | `[KNOWN]` |
| ~50 vacuum tube driver circuits | Operator accounts | `[KNOWN]` |
| 100 KHz base clock, heterodyned | Operator accounts | `[KNOWN]` |
| Up to 74.2 baud operation | Operator accounts | `[KNOWN]` |
| Daily rekey ("BRAVO INDIA") | Operator accounts | `[KNOWN]` |
| Feedback taps modified after USS Pueblo (1968) | NSA publications | `[KNOWN]` |

## What We Reconstructed

The bits we made up. Educated guesses, really. If you squint, they look like engineering decisions.

| Design Choice | Rationale | Classification |
|---------------|-----------|----------------|
| Specific LFSR length | Based on core count and period requirements | `[RECONSTRUCTED]` |
| Feedback polynomial | Chosen from known maximal-length polynomials of era | `[RECONSTRUCTED]` |
| Number of registers | Inferred from combining function security needs | `[RECONSTRUCTED]` |
| Combining function | Based on contemporary cryptographic practice | `[RECONSTRUCTED]` |
| Key scheduling | Plausible mapping from punch card to initial state | `[RECONSTRUCTED]` |

See DEVIATIONS.md for the full confession.

## Historical Context

The TSEC/KW-26 (codename ROMULUS) was developed by NSA in the 1950s to secure fixed teleprinter circuits. Over 14,000 units were produced. It represented the transition from electromechanical rotor machines (like SIGABA) to electronic shift register cryptography. Progress, allegedly.

The KW-26 was compromised when the USS Pueblo was captured by North Korea in January 1968. The crew were unable to destroy all the crypto gear in time, which must have made for some very uncomfortable debriefings. NSA responded by modifying feedback taps in deployed units worldwide, presumably via a memo marked EXTREMELY URGENT and also DO NOT LOSE THIS ONE.

The system was decommissioned in the mid-1980s, replaced by the solid-state TSEC/KG-84. The remaining units were destroyed, melted down, or possibly sold to a museum. One presumes.

## Why This Matters

Besides the obvious joy of implementing something you are explicitly not supposed to know, this reconstruction demonstrates:

1. **LFSR stream cipher principles** - the foundation of much modern cryptography
2. **The transition era** - from rotors to electronics in military cryptography
3. **Operational security** - how key management worked in practice
4. **Why algorithms stay classified** - because someone, somewhere, is probably still using something quite like this and/or someone forgot to do the paperwork.

## Usage

### Command Line

For those who wish to pretend it is 1962 and they have a very important telegram to send:

```bash
# Encrypt a message
python kw26.py encrypt "SECRET MESSAGE"

# Decrypt (using the codes from encrypt output)
python kw26.py decrypt 16 6 10 18 17 2 0 28 22 5 5 11 26 23

# Generate a cryptovariable (the NSA recommends destroying after use)
python kw26.py keygen

# Encrypt with a specific key
python kw26.py encrypt --key b3340ae5327e896c730fe9ffc6b4ad8c "MESSAGE"

# Examine the keystream (for the cryptographically curious)
python kw26.py keystream --bits 100

# Run the demonstration
python kw26.py demo
```

### As a Library

```python
from kw26 import KW26, generate_cryptovariable

# Generate a cryptovariable
# (Real operators had to destroy the card after use. You do not.)
cv = generate_cryptovariable()

# Initialize cipher
cipher = KW26(cv)

# Encrypt Baudot-encoded message
plaintext = "HELLO WORLD"
ciphertext = cipher.encrypt(plaintext)

# Decrypt
# (Assuming your counterpart has the same cryptovariable,
#  which they should, unless someone has made a terrible mistake)
cipher_rx = KW26(cv)  # Fresh cipher, same key
decrypted = cipher_rx.decrypt(ciphertext)
```

## References

The following documents were helpful. Some more than others. Some not at all, really, but they looked impressive in the bibliography.

1. Klein, Melville. "Securing Record Communications: The TSEC/KW-26." NSA, 2003.
2. "A History of U.S. Communications Security" (Boak Lectures). NSA, 1973/1981.
3. "USS Pueblo Cryptographic Damage Assessment." NSA, declassified 2006. (The bits they let us read, anyway.)
4. Schneier, Bruce. "Applied Cryptography." Wiley, 1996. (For when the NSA documents run out of useful information, which is immediately.)

## License

MIT License - See [LICENSE](LICENSE)

Do whatever you like with this code. The NSA certainly cannot complain, given they will not tell us what the real one looked like.

## Author

Zane Hambly, 2025

A person with too much free time and an unreasonable interest in things that blink and go beep.

---

*"The specific algorithm remains classified. The principles are eternal. The documentation is incomplete. The coffee is cold."*
