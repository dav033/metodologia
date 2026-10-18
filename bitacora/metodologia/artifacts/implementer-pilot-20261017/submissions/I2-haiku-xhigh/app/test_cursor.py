import base64
import json
import unittest

from app.cursor import decode_cursor, encode_cursor


def _raw_token(payload_bytes):
    return base64.urlsafe_b64encode(payload_bytes).rstrip(b'=').decode('ascii')


class EncodeCursorTest(unittest.TestCase):
    def test_format_is_unpadded_urlsafe_compact_json(self):
        self.assertEqual(encode_cursor(1, 'a'), _raw_token(b'[1,"a"]'))
        self.assertNotIn('=', encode_cursor(1, 'a'))

    def test_round_trips_unicode_ids(self):
        for row_id in ['ü', '名前', 'emoji-😀', 'a/b+c', 'x' * 500]:
            with self.subTest(row_id=row_id):
                self.assertEqual(decode_cursor(encode_cursor(-7, row_id)), (-7, row_id))

    def test_payload_is_utf8_without_ascii_escapes(self):
        token = encode_cursor(3, 'ü')
        padded = token + '=' * (-len(token) % 4)
        self.assertEqual(base64.urlsafe_b64decode(padded), '[3,"ü"]'.encode('utf-8'))

    def test_rejects_invalid_arguments(self):
        for timestamp, row_id in [(True, 'a'), (1.0, 'a'), ('1', 'a'), (1, ''), (1, None), (1, b'a'), (1, '\ud800')]:
            with self.subTest(timestamp=timestamp, row_id=row_id):
                with self.assertRaises(ValueError):
                    encode_cursor(timestamp, row_id)


class DecodeCursorTest(unittest.TestCase):
    def assertInvalid(self, cursor):
        with self.assertRaises(ValueError):
            decode_cursor(cursor)

    def test_rejects_non_strings_and_empty(self):
        for cursor in [None, b'WzEsImEiXQ', 5, ['WzEsImEiXQ'], '']:
            with self.subTest(cursor=cursor):
                self.assertInvalid(cursor)

    def test_rejects_padding_and_non_urlsafe_characters(self):
        valid = encode_cursor(1, 'a')
        for cursor in [valid + '=', valid + '+', valid + '/', ' ' + valid, valid + '\n', 'W z']:
            with self.subTest(cursor=cursor):
                self.assertInvalid(cursor)

    def test_rejects_malformed_base64(self):
        self.assertInvalid('W')
        self.assertInvalid('WzEsImEiXQJ')
        # Same length as a valid token but with non-zero trailing bits.
        self.assertInvalid('WzEsImEiXR')

    def test_rejects_malformed_json(self):
        for payload in [b'[1,"a"', b'not json', b'', b'\xff\xfe', b'[1,"a"]\x00']:
            with self.subTest(payload=payload):
                self.assertInvalid(_raw_token(payload))

    def test_rejects_wrong_shape(self):
        for payload in [b'{"a":1}', b'1', b'"x"', b'[1]', b'[1,"a","b"]', b'[]', b'null']:
            with self.subTest(payload=payload):
                self.assertInvalid(_raw_token(payload))

    def test_rejects_wrong_types(self):
        for payload in [b'[true,"a"]', b'[1.5,"a"]', b'["1","a"]', b'[null,"a"]', b'[1,1]', b'[1,null]', b'[1,["a"]]']:
            with self.subTest(payload=payload):
                self.assertInvalid(_raw_token(payload))

    def test_rejects_empty_id(self):
        self.assertInvalid(_raw_token(b'[1,""]'))

    def test_rejects_lone_surrogate_id(self):
        self.assertInvalid(_raw_token(b'[1,"\\ud800"]'))

    def test_accepts_standard_json_spacing(self):
        self.assertEqual(decode_cursor(_raw_token(b'[ 1 , "a" ]')), (1, 'a'))

    def test_accepts_negative_and_large_timestamps(self):
        self.assertEqual(decode_cursor(encode_cursor(-(10 ** 30), 'z')), (-(10 ** 30), 'z'))


if __name__ == '__main__':
    unittest.main()
