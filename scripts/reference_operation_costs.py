#!/usr/bin/env python3
"""Fixed portable reference budgets. These prices are not benchmark timings."""
import json

def reference_costs():
    # A: carry-aware add/subtract, including reduced result and register transfers.
    # M: fixed-bit double-and-add modular multiplication; at most two additions per bit.
    # I: Fermat inversion with at most two multiplications per exponent bit.
    # Point price covers normal addition, doubling and exceptional branches.
    # Fp12: 144 coefficient products, 188 additions including polynomial reduction.
    def bounds(bits, words):
        a = 128 * (words + 1)
        m = bits * (2*a + 64) + 128*(words + 1)
        inverse = 2*bits*(m + 64) + 128*(words + 1)
        return a, m, inverse
    a, m, inverse = bounds(256, 1)
    point = inverse + 16*m + 32*a + 4096
    a, m, _ = bounds(381, 2)
    extension = 144*m + 188*a + 65536
    return {'secp256k1-ecdlp': point, 'bls12-381-invert-g1': extension}

if __name__ == '__main__':
    print(json.dumps(reference_costs(), indent=2))
