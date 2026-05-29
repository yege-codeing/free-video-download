"""Generate Douyin web API a_bogus parameter (ported from JoeanAmier/TikTokDownloader)."""

from __future__ import annotations

from random import choice, randint, random
from re import compile as re_compile
from time import time
from urllib.parse import quote, urlencode

from gmssl import func, sm3

__all__ = ["generate_a_bogus"]


class _ABogus:
    __filter = re_compile(r"%([0-9A-F]{2})")
    __arguments = [0, 1, 14]
    __end_string = "cus"
    __reg = [
        1937774191, 1226093241, 388252375, 3666478592,
        2842636476, 372324522, 3817729613, 2969243214,
    ]
    __str = {
        "s4": "Dkdpgh2ZmsQB80/MfvV36XI1R45-WUAlEixNLwoqYTOPuzKFjJnry79HbGcaStCe",
    }

    def __init__(self) -> None:
        self.chunk: list[int] = []
        self.size = 0
        self.reg = self.__reg[:]
        self.ua_code = [
            76, 98, 15, 131, 97, 245, 224, 133, 122, 199, 241, 166, 79, 34, 90, 191,
            128, 126, 122, 98, 66, 11, 14, 40, 49, 110, 110, 173, 67, 96, 138, 252,
        ]
        self.browser = self._generate_browser_info()
        self.browser_code = self._char_code_at(self.browser)
        self.browser_len = len(self.browser)

    @staticmethod
    def _char_code_at(s: str) -> list[int]:
        return [ord(c) for c in s]

    @classmethod
    def _generate_browser_info(cls, platform: str = "Win32") -> str:
        inner_width = randint(1280, 1920)
        inner_height = randint(720, 1080)
        outer_width = randint(inner_width, 1920)
        outer_height = randint(inner_height, 1080)
        values = [
            inner_width, inner_height, outer_width, outer_height,
            0, choice((0, 30)), 0, 0, outer_width, outer_height,
            outer_width, outer_height, inner_width, inner_height,
            24, 24, platform,
        ]
        return "|".join(str(v) for v in values)

    @classmethod
    def _sm3_to_array(cls, data: str | list) -> list[int]:
        raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        digest = sm3.sm3_hash(func.bytes_to_list(raw))
        return [int(digest[i: i + 2], 16) for i in range(0, len(digest), 2)]

    def get_value(self, url_params: dict | str, method: str = "GET") -> str:
        query = urlencode(url_params) if isinstance(url_params, dict) else url_params
        string_1 = self._generate_string_1()
        string_2 = self._generate_string_2(query, method)
        return self._generate_result(string_1 + string_2)

    def _generate_string_1(self) -> str:
        return self._from_char_code(*self._list_1()) + self._from_char_code(*self._list_2()) + self._from_char_code(*self._list_3())

    def _generate_string_2(self, url_params: str, method: str = "GET") -> str:
        start_time = int(time() * 1000)
        end_time = start_time + randint(4, 8)
        params_array = self._sm3_to_array(self._sm3_to_array(url_params + self.__end_string))
        method_array = self._sm3_to_array(self._sm3_to_array(method + self.__end_string))
        payload = self._list_4(
            (end_time >> 24) & 255, params_array[21], self.ua_code[23],
            (end_time >> 16) & 255, params_array[22], self.ua_code[24],
            (end_time >> 8) & 255, end_time & 255,
            (start_time >> 24) & 255, (start_time >> 16) & 255,
            (start_time >> 8) & 255, start_time & 255,
            method_array[21], method_array[22],
            int(end_time / 256 / 256 / 256 / 256), int(start_time / 256 / 256 / 256 / 256),
            self.browser_len,
        )
        payload.extend(self.browser_code)
        payload.append(self._end_check_num(payload))
        return self._rc4_encrypt(self._from_char_code(*payload), "y")

    @staticmethod
    def _from_char_code(*args: int) -> str:
        return "".join(chr(code) for code in args)

    @classmethod
    def _random_list(cls, a: float | None = None, b: int = 170, c: int = 85, d: int = 0, e: int = 0, f: int = 0, g: int = 0) -> list[int]:
        r = a or (random() * 10000)
        v = [r, int(r) & 255, int(r) >> 8]
        v.append(v[1] & b | d)
        v.append(v[1] & c | e)
        v.append(v[2] & b | f)
        v.append(v[2] & c | g)
        return v[-4:]

    @classmethod
    def _list_1(cls) -> list[int]:
        return cls._random_list(None, 170, 85, 1, 2, 5, 45)

    @classmethod
    def _list_2(cls) -> list[int]:
        return cls._random_list(None, 170, 85, 1, 0, 0, 0)

    @classmethod
    def _list_3(cls) -> list[int]:
        return cls._random_list(None, 170, 85, 1, 0, 5, 0)

    @staticmethod
    def _list_4(a, b, c, d, e, f, g, h, i, j, k, m, n, o, p, q, r) -> list[int]:
        return [44, a, 0, 0, 0, 0, 24, b, n, 0, c, d, 0, 0, 0, 1, 0, 239, e, o, f, g, 0, 0, 0, 0, h, 0, 0, 14, i, j, 0, k, m, 3, p, 1, q, 1, r, 0, 0, 0]

    @staticmethod
    def _end_check_num(values: list[int]) -> int:
        result = 0
        for value in values:
            result ^= value
        return result

    @classmethod
    def _generate_result(cls, s: str) -> str:
        alphabet = cls.__str["s4"]
        out: list[str] = []
        for i in range(0, len(s), 3):
            if i + 2 < len(s):
                n = (ord(s[i]) << 16) | (ord(s[i + 1]) << 8) | ord(s[i + 2])
            elif i + 1 < len(s):
                n = (ord(s[i]) << 16) | (ord(s[i + 1]) << 8)
            else:
                n = ord(s[i]) << 16
            for shift, mask in zip(range(18, -1, -6), (0xFC0000, 0x03F000, 0x0FC0, 0x3F)):
                if shift == 6 and i + 1 >= len(s):
                    break
                if shift == 0 and i + 2 >= len(s):
                    break
                out.append(alphabet[(n & mask) >> shift])
        out.append("=" * ((4 - len(out) % 4) % 4))
        return "".join(out)

    @staticmethod
    def _rc4_encrypt(plaintext: str, key: str) -> str:
        s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + s[i] + ord(key[i % len(key)])) % 256
            s[i], s[j] = s[j], s[i]
        i = j = 0
        cipher: list[str] = []
        for ch in plaintext:
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]
            t = (s[i] + s[j]) % 256
            cipher.append(chr(s[t] ^ ord(ch)))
        return "".join(cipher)


def generate_a_bogus(params: dict, user_agent: str = "") -> str:
    del user_agent  # ua_code is pre-baked for Chrome 131 on Windows
    return quote(_ABogus().get_value(params), safe="")
