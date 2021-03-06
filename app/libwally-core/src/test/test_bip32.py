import unittest
from util import *

# These vectors are expressed in binary rather than base 58. The spec base 58
# representation just obfuscates the data we are validating. For example, the
# chain codes in pub/priv results can be seen as equal in the hex data only.
#
# The vector results are the serialized resulting extended key using either the
# contained public or private key. This is not to be confused with private or
# public derivation - these vectors only derive privately.
vec_1 = {
    'seed':     '000102030405060708090a0b0c0d0e0f',

    'm': {
        'pub':  '0488B21E000000000000000000873DFF'
                '81C02F525623FD1FE5167EAC3A55A049'
                'DE3D314BB42EE227FFED37D5080339A3'
                '6013301597DAEF41FBE593A02CC513D0'
                'B55527EC2DF1050E2E8FF49C85C2AB473B21',

        'priv': '0488ADE4000000000000000000873DFF'
                '81C02F525623FD1FE5167EAC3A55A049'
                'DE3D314BB42EE227FFED37D50800E8F3'
                '2E723DECF4051AEFAC8E2C93C9C5B214'
                '313817CDB01A1494B917C8436B35E77E9D71'
    },

    'm/0H': {
        'pub':  '0488B21E013442193E8000000047FDAC'
                'BD0F1097043B78C63C20C34EF4ED9A11'
                '1D980047AD16282C7AE6236141035A78'
                '4662A4A20A65BF6AAB9AE98A6C068A81'
                'C52E4B032C0FB5400C706CFCCC56B8B9C580',

        'priv': '0488ADE4013442193E8000000047FDAC'
                'BD0F1097043B78C63C20C34EF4ED9A11'
                '1D980047AD16282C7AE623614100EDB2'
                'E14F9EE77D26DD93B4ECEDE8D16ED408'
                'CE149B6CD80B0715A2D911A0AFEA0A794DEC'
    },

    'm/0H/1': {
        'pub':  '0488B21E025C1BD648000000012A7857'
                '631386BA23DACAC34180DD1983734E44'
                '4FDBF774041578E9B6ADB37C1903501E'
                '454BF00751F24B1B489AA925215D66AF'
                '2234E3891C3B21A52BEDB3CD711C6F6E2AF7',

        'priv': '0488ADE4025C1BD648000000012A7857'
                '631386BA23DACAC34180DD1983734E44'
                '4FDBF774041578E9B6ADB37C19003C6C'
                'B8D0F6A264C91EA8B5030FADAA8E538B'
                '020F0A387421A12DE9319DC93368B34BC442'
    },

    'm/0H/1/2H': {
        'pub':  '0488B21E03BEF5A2F98000000204466B'
                '9CC8E161E966409CA52986C584F07E9D'
                'C81F735DB683C3FF6EC7B1503F0357BF'
                'E1E341D01C69FE5654309956CBEA5168'
                '22FBA8A601743A012A7896EE8DC2A5162AFA',

        'priv': '0488ADE403BEF5A2F98000000204466B'
                '9CC8E161E966409CA52986C584F07E9D'
                'C81F735DB683C3FF6EC7B1503F00CBCE'
                '0D719ECF7431D88E6A89FA1483E02E35'
                '092AF60C042B1DF2FF59FA424DCA25814A3A'
    }
}

class BIP32Tests(unittest.TestCase):

    SERIALIZED_LEN = 4 + 1 + 4 + 4 + 32 + 33
    KEY_PRIVATE, KEY_PUBLIC = 0, 1

    VER_MAIN_PUBLIC = 0x0488B21E
    VER_MAIN_PRIVATE = 0x0488ADE4
    VER_TEST_PUBLIC = 0x043587CF
    VER_TEST_PRIVATE = 0x04358394


    def unserialize_key(self, buf, buf_len):
        key_out = ext_key()
        ret = bip32_key_unserialize(buf, buf_len, byref(key_out))
        return ret, key_out

    def get_test_master_key(self, vec):
        seed, seed_len = make_cbuffer(vec['seed'])
        master = ext_key()
        ret = bip32_key_from_seed(seed, seed_len,
                                  self.VER_MAIN_PRIVATE, byref(master))
        self.assertEqual(ret, 0)
        return master

    def get_test_key(self, vec, path, typ):
        buf, buf_len = make_cbuffer(vec[path][typ])
        ret, key_out = self.unserialize_key(buf, self.SERIALIZED_LEN)
        self.assertEqual(ret, 0)
        return key_out

    def derive_key(self, parent, child_num, kind):
        key_out = ext_key()
        ret = bip32_key_from_parent(byref(parent), child_num,
                                    kind, byref(key_out))
        self.assertEqual(ret, 0)

        # Verify that path derivation matches also
        p_key_out = self.derive_key_by_path(parent, [child_num], kind)
        typ = 'pub' if kind == self.KEY_PUBLIC else 'priv'
        self.compare_keys(p_key_out, key_out, typ)
        return key_out

    def derive_key_by_path(self, parent, path, kind):
        key_out = ext_key()
        c_path = (c_uint * len(path))()
        for i, n in enumerate(path):
            c_path[i] = n
        ret = bip32_key_from_parent_path(byref(parent), c_path, len(path),
                                         kind, byref(key_out))
        self.assertEqual(ret, 0)
        return key_out

    def compare_keys(self, key, expected, typ):
        self.assertEqual(h(key.chain_code), h(expected.chain_code))
        expected_cmp = getattr(expected, typ + '_key')
        key_cmp = getattr(key, typ + '_key')
        self.assertEqual(h(key_cmp), h(expected_cmp))
        self.assertEqual(key.depth, expected.depth)
        self.assertEqual(key.child_num, expected.child_num)
        self.assertEqual(h(key.chain_code), h(expected.chain_code))
        # These would be more useful tests if there were any public
        # derivation test vectors
        self.assertEqual(h(key.hash160), h(expected.hash160))
        # We can only compare the first 4 bytes of the parent fingerprint
        # Since that is all thats serialized.
        # FIXME: Implement bip32_key_set_parent and test it here
        fingerprint = lambda k: h(k.parent160)[0:8]
        self.assertEqual(fingerprint(key), fingerprint(expected))


    def test_serialisation(self):

        # Try short, correct, long lengths. Trimming 8 chars is the correct
        # length because the vector value contains 4 check bytes at the end.
        for trim, expected in [(0, WALLY_EINVAL), (8, WALLY_OK), (16, WALLY_EINVAL)]:
            serialized_hex = vec_1['m']['priv'][0:-trim]
            buf, buf_len = make_cbuffer(serialized_hex)
            ret, key_out = self.unserialize_key(buf, buf_len)
            self.assertEqual(ret, expected)
            if ret == 0:
                # Check this key serializes back to the same representation
                # FIXME: Add full test cases for the serialisation code including errors
                buf, buf_len = make_cbuffer('0' * len(serialized_hex))
                ret = bip32_key_serialize(key_out, self.KEY_PRIVATE,
                                          buf, buf_len)
                self.assertEqual(ret, 0)
                self.assertEqual(h(buf).upper(), utf8(serialized_hex))

        # Check correct and incorrect version numbers as well
        # as mismatched key types and versions
        ver_cases = [(self.VER_MAIN_PUBLIC,  'pub',  WALLY_OK),
                     (self.VER_MAIN_PUBLIC,  'priv', WALLY_EINVAL),
                     (self.VER_MAIN_PRIVATE, 'pub',  WALLY_EINVAL),
                     (self.VER_MAIN_PRIVATE, 'priv', WALLY_OK),
                     (self.VER_TEST_PUBLIC,  'pub',  WALLY_OK),
                     (self.VER_TEST_PUBLIC , 'priv', WALLY_EINVAL),
                     (self.VER_TEST_PRIVATE, 'pub',  WALLY_EINVAL),
                     (self.VER_TEST_PRIVATE, 'priv', WALLY_OK),
                     (0x01111111,            'pub',  WALLY_EINVAL),
                     (0x01111111,            'priv', WALLY_EINVAL)]

        for ver, typ, expected in ver_cases:
            no_ver = vec_1['m'][typ][8:-8]
            v_str = '0' + hex(ver)[2:]
            buf, buf_len = make_cbuffer(v_str + no_ver)
            ret, _ = self.unserialize_key(buf, buf_len)
            self.assertEqual(ret, expected)


    def test_key_from_seed(self):

        seed, seed_len = make_cbuffer(vec_1['seed'])
        key_out = ext_key()

        # Only private key versions can be used
        ver_cases = [(self.VER_MAIN_PUBLIC,   WALLY_EINVAL),
                     (self.VER_MAIN_PRIVATE,  WALLY_OK),
                     (self.VER_TEST_PUBLIC,   WALLY_EINVAL),
                     (self.VER_TEST_PRIVATE,  WALLY_OK)]
        for ver, expected in ver_cases:
            ret = bip32_key_from_seed(seed, seed_len, ver, byref(key_out))
            self.assertEqual(ret, expected)


    def test_bip32_vectors(self):

        # BIP32 Test vector 1
        master = self.get_test_master_key(vec_1)

        # Chain m:
        for typ in ['pub', 'priv']:
            expected = self.get_test_key(vec_1, 'm', typ)
            self.compare_keys(master, expected, typ)

        derived = master
        for path, i in [('m/0H', 0x80000000),
                        ('m/0H/1', 1),
                        ('m/0H/1/2H', 0x80000002)]:

            # Derive a public and private child. Verify that the private child
            # contains the public and private published vectors. Verify that
            # the public child matches the public vector and has no private
            # key. Finally, check that the child holds the correct parent hash.
            parent160 = derived.hash160
            derived_pub = self.derive_key(derived, i, self.KEY_PUBLIC)
            derived = self.derive_key(derived, i, self.KEY_PRIVATE)
            for typ in ['pub', 'priv']:
                expected = self.get_test_key(vec_1, path, typ)
                self.compare_keys(derived, expected, typ)
                if typ == 'pub':
                    self.compare_keys(derived_pub, expected, typ)
                    # A neutered private key is indicated by
                    # BIP32_FLAG_KEY_PUBLIC (0x1) as its first byte.
                    self.assertEqual(h(derived_pub.priv_key), '01' + '00' * 32)
                self.assertEqual(h(derived.parent160), h(parent160))


    def test_public_derivation_identities(self):

        # Start with BIP32 Test vector 1
        master = self.get_test_master_key(vec_1)

        # Derive the same child public and private keys from master
        pub = self.derive_key(master, 1, self.KEY_PUBLIC)
        priv = self.derive_key(master, 1, self.KEY_PRIVATE)

        # From the private child we can derive public and private keys
        priv_pub = self.derive_key(priv, 1, self.KEY_PUBLIC)
        priv_priv = self.derive_key(priv, 1, self.KEY_PRIVATE)

        # From the public child we can only derive a public key
        pub_pub = self.derive_key(pub, 1, self.KEY_PUBLIC)
        # Verify that trying to derive a private key doesn't work
        key_out = ext_key()
        ret = bip32_key_from_parent(byref(pub), 1,
                                    self.KEY_PRIVATE, byref(key_out))
        self.assertEqual(ret, WALLY_EINVAL)

        # Now our identities:
        # The children share the same public key
        self.assertEqual(h(pub.pub_key), h(priv.pub_key))
        # The grand-children share the same public key
        self.assertEqual(h(priv_pub.pub_key), h(priv_priv.pub_key))
        self.assertEqual(h(priv_pub.pub_key), h(pub_pub.pub_key))
        # The children and grand-children do not share the same public key
        self.assertNotEqual(h(pub.pub_key), h(priv_pub.pub_key))

        # Test path derivation with multiple child elements
        for kind, typ, expected in [(self.KEY_PUBLIC,  'pub',  pub_pub),
                                    (self.KEY_PRIVATE, 'priv', priv_priv)]:
            path_derived = self.derive_key_by_path(master, [1, 1], kind)
            self.compare_keys(path_derived, expected, typ)

if __name__ == '__main__':
    unittest.main()
