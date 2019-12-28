import os
import tempfile
import unittest

from server import app, db_init


class ServerTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config["DATABASE"] = tempfile.mkstemp()
        self.client = app.test_client()
        db_init()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config["DATABASE"])

    def test_flow(self):
        data = {
            "one": 1,
            "truthy": True,
            "a string": "yes, a string 🎉",
        }
        KEY = "my/test/key1"
        PATH = f"/{KEY}"

        # it should not previously exist
        res = self.client.get(PATH)
        self.assertEqual(res.status_code, 404)
        res_json = res.get_json()
        self.assertIn("error", res_json)
        self.assertIn("status", res_json)

        # deleting should be 404
        res = self.client.delete(PATH)
        self.assertEqual(res.status_code, 404)
        res_json = res.get_json()
        self.assertIn("error", res_json)
        self.assertIn("status", res_json)

        # now we create it
        res = self.client.post(PATH, json=data)
        self.assertEqual(res.status_code, 200)
        res_json = res.get_json()
        self.assertEqual(res_json["value"]["one"], 1)
        self.assertEqual(res_json["key"], KEY)

        # now it should exist
        res = self.client.get(PATH)
        self.assertEqual(res.status_code, 200)
        res_json = res.get_json()
        self.assertEqual(res_json["a string"], "yes, a string 🎉")

        # and delete it
        res = self.client.delete(PATH)
        self.assertEqual(res.status_code, 204)
        res_json = res.get_json()
        self.assertIsNone(res_json)

        # now it should no longer exist
        res = self.client.get(PATH)
        self.assertEqual(res.status_code, 404)
        res_json = res.get_json()
        self.assertIn("error", res_json)
        self.assertIn("status", res_json)

    def test_updates(self):
        data = {"number": 1}
        KEY = "my/test/key2"
        PATH = f"/{KEY}"

        # check that it doesn't exist
        res = self.client.get(PATH)
        self.assertEqual(res.status_code, 404)

        # now create it
        res = self.client.post(PATH, json=data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["value"]["number"], 1)

        # check that we can retrieve it correctly
        res = self.client.get(PATH)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["number"], 1)

        # now post to it again
        data = {"number": 42}
        res = self.client.post(PATH, json=data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["value"]["number"], 42)

        # now post to it yet again
        data = {"number": 123}
        res = self.client.post(PATH, json=data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["value"]["number"], 123)

        # check that it has actually been updated
        res = self.client.get(PATH)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["number"], 123)

    def test_invalid_input(self):
        # not json
        res = self.client.post("/test/key/invalid", data="{XJDE(&*@(CENTHUO")
        self.assertEqual(res.status_code, 400)

        # the base url is not allowed to be posted to
        res = self.client.post("/", json={"hello": True})
        self.assertEqual(res.status_code, 405)

    def test_api_spec_endpoints(self):
        res = self.client.get("/api/spec")
        self.assertEqual(res.status_code, 200)
        self.assertIn("version", res.get_json()["info"])

        res = self.client.get("/docs/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"swagger-ui", res.get_data())

        # the base url redirects to the docs
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/docs", res.location)


if __name__ == "__main__":
    unittest.main()
