"""
MIT License

Copyright (c) 2022 Visperi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Union, List
import datetime


class _CacheItem:

    def __init__(self, name: str, value: object, last_hit: datetime.datetime = None):
        self.name = name
        self.original_reference = value

        if last_hit is None:
            self.last_hit = datetime.datetime.utcnow()
        elif isinstance(last_hit, datetime.datetime):
            self.last_hit = last_hit
        else:
            self.last_hit = self._timestamp_to_datetime(last_hit)

    def __str__(self):
        return self.name

    @staticmethod
    def _timestamp_to_datetime(ts: float) -> datetime.datetime:
        return datetime.datetime.utcfromtimestamp(ts)


class Cache:

    def __init__(self, name: str = None, item_lifetime: Union[int, dict] = None,
                 cache: list = None):
        """
        :param name: Optional identifier for the cache
        :param item_lifetime: Lifetime for cache items. Deprecated entries are removed on synchronisation. None
                              means infinite lifetime. Integer is converted to hours, dictionary can have keys
                              'days', 'hours' and 'minutes'.
        :param cache: A premade cache list of objects. If none, an empty cache is created
        """
        self.name = name
        self._ITEM_LIFETIME = None
        self._CACHE = []

        if item_lifetime is not None:
            self.set_lifetime(item_lifetime)

        if cache is not None:
            self.add(cache)

    def set_lifetime(self, lifetime: Union[int, dict]):
        """
        Set lifetime for the cache items. Items exceeding their lifetime are removed from cache on synchronisation.
        :param lifetime: Integer, None or dictionary giving the item lifetime. Integers are converted to hours and
                              dictionary can have keys 'days', 'hours' and 'minutes' that are converted into appropriate
                              values. None means infinite lifetime.
        """
        if lifetime is None:
            self._ITEM_LIFETIME = None
            return

        if isinstance(lifetime, int):
            days = 0
            hours = lifetime
            minutes = 0
        else:
            try:
                days = lifetime["days"]
            except KeyError:
                days = 0
            try:
                hours = lifetime["hours"]
            except KeyError:
                hours = 0
            try:
                minutes = lifetime["minutes"]
            except KeyError:
                minutes = 0

        if days <= 0 or hours <= 0 or minutes <= 0:
            raise ValueError("Lifetime must be a positive value or None.")

        self._ITEM_LIFETIME = datetime.timedelta(days=days, hours=hours, minutes=minutes)

    def __str__(self) -> str:
        """
        Convert the current cache items into a string. Items are separated with attribute entry_separator.
        If this is None, the items are separated by comma.
        :return: Cache items as a string
        """

        cache_items = [str(item) for item in self.get_items()]
        res = ", ".join(cache_items)
        return f"Cache({res})"

    def __repr__(self):
        return str(self)

    def __len__(self) -> int:
        return len(self._CACHE)

    def __contains__(self, item: object) -> bool:
        for cache_item in self._CACHE:
            if item is cache_item.original_reference or item == cache_item.original_reference:
                return True
        return False

    def get_items(self) -> list:
        """
        Get list of cache items.
        :return: List of cache items
        """
        return [item.original_reference for item in self._CACHE]

    def clear(self):
        """
        Clear contents of the cache
        """
        self._CACHE.clear()

    def _find_cache_item(self, obj: object) -> _CacheItem:

        for item in self._CACHE:
            if obj is item.original_reference:
                return item

        raise ValueError(f"Could not find item {str(obj)} from cache.")

    def _add_item(self, cache_item: object):
        timestamp = datetime.datetime.utcnow()

        if cache_item not in self:
            name = str(cache_item)
            new_item = _CacheItem(name, cache_item, last_hit=timestamp)
            self._CACHE.append(new_item)
        else:
            item = self._find_cache_item(cache_item)
            item.last_hit = timestamp

    def add(self, cache_item: Union[object, List[object]]):
        """
        Add new content to the cache. Skip contents that already exists in cache.
        :param cache_item: Content(s) that should be added. Single object or list of objects
        """
        if isinstance(cache_item, list):
            for item in cache_item:
                self._add_item(item)
        else:
            self._add_item(cache_item)

    def _delete_item(self, cache_item: object):
        deleted_item = self._find_cache_item(cache_item)
        self._CACHE.remove(deleted_item)

    def delete(self, cache_item: Union[object, List[object]]):
        """
        Delete a single item or list of items from the cache.
        :param cache_item: Single object or list of objects
        """
        if isinstance(cache_item, list):
            for item in cache_item:
                self._delete_item(item)
        else:
            self._delete_item(cache_item)

    def delete_deprecated(self) -> int:
        """
        Delete items that have exceeded their lifetime from cache. Nothing will be deleted if lifetime is None.
        :return: Number of items deleted from cache
        """
        current_time = datetime.datetime.utcnow()
        deprecated_items = []

        if self._ITEM_LIFETIME is None:
            print("Nothing to delete. Item lifetime is infinite.")
            return 0

        for item in self._CACHE:
            diff = current_time - item.last_hit
            if diff >= self._ITEM_LIFETIME:
                deprecated_items.append(item)

        self.delete(deprecated_items)
        return len(deprecated_items)
