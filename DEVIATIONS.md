# KW-26 Reconstruction: Deviation Documentation

This document meticulously records every design decision, distinguishing between declassified facts and reconstructed elements.

---

## 1. LFSR Configuration

### 1.1 Number of Shift Registers

**Status:** `[RECONSTRUCTED]`

**What we know:**
- The KW-26 contained ~800 magnetic cores
- Single LFSR systems are cryptographically weak (Berlekamp-Massey attack)
- NSA would have known this in the 1950s

**Our choice:** Three LFSRs with a nonlinear combining function

**Rationale:**
- Multiple LFSRs with nonlinear combining was state-of-art for 1950s
- Three registers provide security against correlation attacks
- 800 cores could support three ~250-bit registers with control logic
- The "Geffe generator" (1967) used three LFSRs - NSA likely knew this earlier

**Confidence:** Medium - could be 2, 3, 4, or more registers

---

### 1.2 LFSR Lengths

**Status:** `[RECONSTRUCTED]`

**What we know:**
- Must produce keystream at 74.2 baud continuously
- Daily rekey implies period must exceed 24 hours of traffic
- At 74.2 baud: 74.2 × 60 × 60 × 24 = ~6.4 million bits/day

**Our choice:**
- LFSR-A: 31 bits (period 2^31 - 1 = 2.1 billion)
- LFSR-B: 29 bits (period 2^29 - 1 = 537 million)
- LFSR-C: 23 bits (period 2^23 - 1 = 8.4 million)

**Rationale:**
- Combined period is LCM of individual periods (astronomical)
- Prime-length registers avoid synchronization
- Total: 83 bits of state, leaving ~700 cores for control logic
- These lengths have known maximal-length polynomials from 1950s literature

**Confidence:** Low - actual lengths unknown

---

### 1.3 Feedback Polynomials

**Status:** `[RECONSTRUCTED]`

**What we know:**
- Must be primitive (maximal-length) polynomials
- Taps were modified after Pueblo incident (1968)
- NSA had access to tables of primitive polynomials

**Our choice:**
```
LFSR-A (31-bit): x^31 + x^3 + 1
LFSR-B (29-bit): x^29 + x^2 + 1
LFSR-C (23-bit): x^23 + x^5 + 1
```

**Rationale:**
- These are known primitive polynomials from the era
- Sparse taps (few XOR operations) match vacuum tube constraints
- Different tap positions between registers

**Confidence:** Very Low - the actual polynomials are the core secret

---

## 2. Combining Function

### 2.1 Nonlinear Combiner

**Status:** `[RECONSTRUCTED]`

**What we know:**
- Pure XOR of LFSR outputs would be linear and weak
- NSA cryptographers knew about correlation attacks
- Hardware used vacuum tubes (limited gate complexity)

**Our choice:** Majority function with XOR

```python
def combine(a, b, c):
    # Majority function: output 1 if 2 or more inputs are 1
    majority = (a & b) | (b & c) | (a & c)
    # XOR with third register for additional nonlinearity
    return majority ^ c
```

**Rationale:**
- Majority function is nonlinear but simple to implement
- Common in 1950s-60s stream cipher literature
- Implementable with a few vacuum tubes
- Provides correlation immunity

**Confidence:** Low - many combining functions possible

---

## 3. Key Loading (Cryptovariable)

### 3.1 Punch Card Format

**Status:** `[KNOWN]` (partial)

**What we know:**
- 45-column Remington Rand (UNIVAC) format
- Round holes (not rectangular IBM)
- Card physically destroyed upon insertion
- One card = one day's cryptovariable

**What we don't know:**
- Exact bit mapping from card to LFSR initial states
- Whether any key scheduling/expansion occurred
- Error detection format on card

---

### 3.2 Key Expansion

**Status:** `[RECONSTRUCTED]`

**Our choice:** Direct load with parity check

```
Card columns 1-31:  LFSR-A initial state
Card columns 32-45: LFSR-B bits 1-14
                    LFSR-B bits 15-29 derived via expansion
LFSR-C:             Derived from hash of A and B
```

**Rationale:**
- 45 columns at ~6 bits each = ~270 bits of key material
- More than enough for 83 bits of LFSR state
- Some expansion likely for error detection/redundancy

**Confidence:** Very Low - complete speculation

---

## 4. Baudot Interface

### 4.1 Character Encoding

**Status:** `[KNOWN]`

**Facts:**
- Standard 5-bit ITA2 Baudot code
- Keystream XORed with plaintext bits
- Start/stop bits handled separately (not encrypted)

**Implementation:** Direct ITA2 Baudot as documented in standards

**Confidence:** High - this is standard teleprinter operation

---

### 4.2 Continuous Operation

**Status:** `[KNOWN]`

**Facts:**
- KW-26 transmitted continuous keystream
- Idle pattern sent when no traffic
- Provides traffic flow security

**Implementation:** Continuous keystream generation, XOR applied to all bits

**Confidence:** High - explicitly documented

---

## 5. Clocking

### 5.1 Clock Generation

**Status:** `[KNOWN]` (partial)

**What we know:**
- 100 KHz base oscillator
- Heterodyned to operational frequency
- Adjustable via trimmer

**Our choice:** Simple synchronous clocking of all registers

**Rationale:**
- Asynchronous/irregular clocking would add complexity
- No evidence of clock control in available documentation
- Simpler design matches 1950s engineering

**Confidence:** Medium - could have been more complex

---

## 6. Synchronization

### 6.1 Transmit/Receive Sync

**Status:** `[RECONSTRUCTED]`

**What we know:**
- Both ends must produce identical keystream
- Requires identical cryptovariable and initialization

**Our choice:** Count from midnight (00:00:00) each day

**Rationale:**
- With daily rekey, both units start from same state
- Time-based offset prevents replay attacks
- Simple to implement with available hardware

**Confidence:** Low - actual sync mechanism unknown

---

## Summary of Confidence Levels

| Component | Confidence | Notes |
|-----------|------------|-------|
| LFSR-based design | **High** | Explicitly documented |
| Baudot XOR | **High** | Standard operation |
| Continuous keystream | **High** | Explicitly documented |
| Multiple LFSRs | **Medium** | Cryptographically necessary |
| Clock mechanism | **Medium** | Partially documented |
| LFSR lengths | **Low** | Inferred from constraints |
| Combining function | **Low** | Many possibilities |
| Key expansion | **Very Low** | Speculation |
| Feedback polynomials | **Very Low** | Core secret |

---

## Version History

- v0.1 (2025-01-01): Initial reconstruction design

---

*This document will be updated as additional declassified information becomes available.*
