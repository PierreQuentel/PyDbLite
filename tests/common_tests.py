# -*- coding: utf-8 -*-
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.resetwarnings()


class Generic(object):
    """Generic class for unit testing :mod:`pydblite.pydblite` and :mod:`pydblite.sqlite`"""

    def test_create_index(self):
        indices = self.filter_db.get_indices()
        self.assertEqual(indices, [])
        self.filter_db.create_index("name")
        indices = self.filter_db.get_indices()
        self.assertEqual(indices, ["name"])

        self.filter_db.create_index("active")
        indices = self.filter_db.get_indices()
        self.assertTrue("active" in indices)
        self.assertTrue("name" in indices)
        self.assertEqual(len(indices), 2)

    def test_delete_index(self):
        self.filter_db.create_index("name")
        self.filter_db.create_index("active")
        self.filter_db.delete_index("name")
        self.assertEqual(self.filter_db.get_indices(), ["active"])
        self.filter_db.delete_index("active")
        self.assertEqual(self.filter_db.get_indices(), [])

    def test_add_field(self):
        self.setup_db_for_filter()
        self.filter_db.add_field('age', column_type='INTEGER')

        # Check the value of age field for record that existed
        # before the new field was adde
        record = self.filter_db(unique_id=4)[0]
        self.assertEqual(record["age"], None)

        # Check value of age field for new record with age value
        status = {"unique_id": 110, 'age': 10}
        self.filter_db.insert(**status)
        record = self.filter_db(unique_id=110)[0]
        self.assertEqual(record["age"], 10)

        # Check value of age field for new record with no age value
        status = {"unique_id": 111}
        self.filter_db.insert(**status)
        record = self.filter_db(unique_id=111)[0]
        self.assertEqual(record["age"], None)

    def test_add_field_with_default_value(self):
        self.setup_db_for_filter()
        self.filter_db.add_field('age', column_type='INTEGER', default=5)

        # Check the value of age field for record that existed
        # before the new field was adde
        record = self.filter_db(unique_id=4)[0]
        self.assertEqual(record["age"], 5)

        # Check value of age field for new record with age value
        status = {"unique_id": 110, 'age': 10}
        self.filter_db.insert(**status)
        record = self.filter_db(unique_id=110)[0]
        self.assertEqual(record["age"], 10)

        # Check value of age field for new record with no age value
        status = {"unique_id": 111}
        record_id = self.filter_db.insert(**status)
        record = self.filter_db[record_id]
        self.assertEqual(record["age"], 5)

    def test_insert(self):
        status = {"unique_id": 1}
        res = self.filter_db.insert(**status)
        # First database record id should be 0
        self.assertEqual(res, self.first_record_id)
        self.assertEqual(len(self.filter_db), 1)
        status = {"unique_id": 2}
        res = self.filter_db.insert(**status)
        # Second database record id should be 1
        self.assertEqual(res, self.first_record_id + 1)
        self.assertEqual(len(self.filter_db), 2)

    def test_insert_values_in_order(self):
        status = (1,)
        res = self.filter_db.insert(*status)
        # First database record id should be 0
        self.assertEqual(res, self.first_record_id)
        self.assertEqual(len(self.filter_db), 1)
        status = (2, "name_value", False)
        res = self.filter_db.insert(*status)

        # Second database record id should be 1
        self.assertEqual(res, self.first_record_id + 1)
        self.assertEqual(len(self.filter_db), 2)
        rec = self.filter_db[res]
        # Verify that the values inserted in order are correct
        self.assertEqual(rec["unique_id"], status[0])
        self.assertEqual(rec["name"], status[1])
        self.assertEqual(rec["active"], status[2])

    def test_update(self):
        self.setup_db_for_filter()
        record = self.filter_db(unique_id=4)[0]
        self.filter_db.update(record, name=record['name'].upper())
        self.assertEqual(self.filter_db[record["__id__"]]["name"], "TEST4")

    def test_select(self):
        self.setup_db_for_filter()
        record = self.filter_db(unique_id=1)[0]
        self.assertTrue(record['active'] == 1 or record['active'] is True)
        self.assertEqual(record["unique_id"], 1)
        self.assertEqual(record["name"], 'Test0')

    def test_select_unicode(self):
        status = {"unique_id": 1, "active": True, "name": u"éçùï"}
        self.filter_db.insert(**status)
        self.assertEqual(self.filter_db(name='foo'), [])
        self.assertEqual(self.filter_db(name=u'éçùï')[0]["unique_id"], 1)

    def test_iter(self):
        self.setup_db_for_filter()
        self.assertEqual(len([x for x in self.filter_db]), len(self.filter_db))
        records = self.filter_db()
        for r in records:
            self.assertEqual([x for x in self.filter_db if x['unique_id'] == r['unique_id']],
                             self.filter_db(unique_id=r['unique_id']))
            self.assertEqual([x for x in self.filter_db if x['name'] == r['name']],
                             self.filter_db(name=r['name']))

    def test_fetch(self):
        torrent_count = 10
        for i in range(torrent_count):
            status = {"unique_id": i}
            self.filter_db.insert(**status)

        for i in range(torrent_count):
            records = self.filter_db(unique_id=i)
            self.assertEqual(records[0]["unique_id"], i)

    def test_delete(self):
        status = {"unique_id": 1}
        self.filter_db.insert(**status)
        status = {"unique_id": 2}
        self.filter_db.insert(**status)

        records = self.filter_db(unique_id=1)
        deleted_count = self.filter_db.delete(records[0])
        self.assertEqual(1, deleted_count)

        records = self.filter_db(unique_id=1)
        self.assertEqual(records, [])
        # Number of entries left should be 1
        self.assertEqual(len(self.filter_db()), 1)

        records = self.filter_db(unique_id=2)
        deleted_count = self.filter_db.delete(records[0])
        self.assertEqual(len(self.filter_db()), 0)

    def test_del(self):
        status = {"unique_id": 1}
        rec = self.filter_db.insert(**status)
        del self.filter_db[rec]
        self.assertEqual(self.filter_db(name='non-existent'), [])
        self.assertEqual(len(self.filter_db), 0)

    def reset_status_values_for_filter(self):
        self.status = []
        self.status.append({"unique_id": 1, "active": True, "name": "Test0"})
        self.status.append({"unique_id": 2, "active": True, "name": "Test0"})
        self.status.append({"unique_id": 3, "active": True, "name": "test0"})
        self.status.append({"unique_id": 4, "active": True, "name": "Test4"})
        self.status.append({"unique_id": 5, "active": False, "name": "Test4"})
        self.status.append({"unique_id": 6, "active": False, "name": "Test6"})
        self.status.append({"unique_id": 7, "active": False, "name": "Test7"})

    def setup_db_for_filter(self):
        self.reset_status_values_for_filter()
        res = self.filter_db.insert(self.status)
        self.assertTrue(res is None or res == 7)  # Depends on the database driver...

    def test_filter_len(self):
        self.setup_db_for_filter()
        f = self.filter_db.filter()
        self.assertEqual(len(f), len(self.status))

    def test_filter_equals(self):
        self.setup_db_for_filter()
        self.assertEqual(len((self.filter_db("active") == True)), 4)  # noqa

    def test_filter_not_equals(self):
        self.setup_db_for_filter()
        self.assertEqual(len((self.filter_db("active") != True)), 3)  # noqa

    def test_filter_in(self):
        """Test IN ( == with a list"""
        self.setup_db_for_filter()
        self.assertEqual(len(self.filter_db("name") == ["Test4", "Test7"]), 3)

    def test_filter_greater(self):
        self.setup_db_for_filter()
        self.assertEqual(len((self.filter_db("unique_id") > 4)), 3)

    def test_filter_greater_equals(self):
        self.setup_db_for_filter()
        self.assertEqual(len((self.filter_db("unique_id") >= 4)), 4)

    def test_filter_less(self):
        self.setup_db_for_filter()
        self.assertEqual(len((self.filter_db("unique_id") < 3)), 2)

    def test_filter_less_equals(self):
        self.setup_db_for_filter()
        self.assertEqual(len((self.filter_db("unique_id") <= 3)), 3)

    def test_filter_ilike(self):
        """Test text case sensitive"""
        self.setup_db_for_filter()
        self.assertEqual(len(self.filter_db("name").ilike("Test")), 6)
        self.assertEqual(len(self.filter_db("name").ilike("Test0")), 2)

    def test_filter_like(self):
        """Test text case insensitive"""
        self.setup_db_for_filter()
        self.assertEqual(len(self.filter_db("name").like("Test")), 7)
        self.assertEqual(len(self.filter_db("name").like("Test0")), 3)

    def test_filter_and(self):
        """Test AND"""
        self.setup_db_for_filter()
        f = (self.filter_db.filter() &
             (self.filter_db.filter(key="name") == "Test4"))
        self.assertEqual(str(f), "name = 'Test4'")

        f = ((self.filter_db.filter(key="name") == "Test4") &
             (self.filter_db.filter(key="active") == False))  # noqa
        self.assertEqual(str(f), "((active = 0) AND (name = 'Test4'))")
        self.assertEqual(len(f), 1)

    def test_filter_or(self):
        """Test OR"""
        self.setup_db_for_filter()
        f = (self.filter_db.filter() |
             (self.filter_db.filter(key="name") == "Test4"))
        self.assertEqual(str(f), "name = 'Test4'")

        f = ((self.filter_db.filter(key="name") == "Test4") |
             (self.filter_db.filter(key="active") == False))  # noqa
        self.assertEqual(str(f), "((active = 0) OR (name = 'Test4'))")
        self.assertEqual(len(f), 4)

    def test_len_with_filter(self):
        self.setup_db_for_filter()
        f = self.filter_db.filter()
        f |= (self.filter_db("active") == True)  # noqa
        self.assertEquals(self.filter_db._len(f), 4)

    def test_len_with_filter_non_matching(self):
        self.setup_db_for_filter()
        f = self.filter_db.filter()
        f |= (self.filter_db("unique_id") == -1)  # Will not match any entries
        self.assertEqual(self.filter_db._len(f), 0)

    def test_filter_get_unique_ids(self):
        self.setup_db_for_filter()
        ids = self.filter_db.get_unique_ids("name")
        self.assertEqual(ids, set(['Test0', 'Test6', 'Test4', 'Test7', 'test0']))

    def test_filter_get_unique_ids_with_filter(self):
        self.setup_db_for_filter()
        f = self.filter_db.filter()
        f |= (self.filter_db("active") == True)  # noqa
        ids = self.filter_db.get_unique_ids("name", f)
        self.assertEquals(ids, set(['Test0', 'Test4', 'test0']))

    def test_filter_get_unique_ids_with_filter_non_matching(self):
        self.setup_db_for_filter()
        f = self.filter_db.filter() | (self.filter_db("unique_id") == -1)  # Will not match any
        ids = self.filter_db.get_unique_ids("name", f)
        self.assertEqual(ids, set())

    def make_group_count_result(self, key, test_key=None, test_val=None):
        counts = {}
        for e in self.status:
            if test_key and e[test_key] != test_val:
                continue
            counts[e[key]] = counts.get(e[key], 0) + 1
        return counts

    def test_get_group_count(self):
        self.setup_db_for_filter()
        counts = self.make_group_count_result("name")
        result = self.filter_db.get_group_count("name")
        for name, count in result:
            self.assertEqual(count, counts[name])

    def test_get_group_count_with_filter(self):
        self.setup_db_for_filter()
        counts = self.make_group_count_result("name", test_key="active", test_val=True)
        f = self.filter_db.filter() | (self.filter_db("active") == True)  # noqa
        result = self.filter_db.get_group_count("name", f)
        for name, count in result:
            self.assertEqual(count, counts[name])

    def test_get_group_count_with_filter_non_matching(self):
        self.setup_db_for_filter()
        counts = self.make_group_count_result("name", test_key="unique_id", test_val=-1)
        f = self.filter_db.filter() | (self.filter_db("unique_id") == -1)
        result = self.filter_db.get_group_count("name", f)
        for name, count in result:
            self.assertEqual(count, counts[name])
