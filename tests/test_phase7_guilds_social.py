import os
import sys
import unittest
import uuid

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.utils.storage import update_user, get_user
from modules.guilds.guild_manager import GuildManager
from modules.social.social_manager import SocialManager


class TestPhase7GuildsAndSocial(unittest.TestCase):
    def setUp(self):
        self.gm = GuildManager.get_instance()
        self.sm = SocialManager.get_instance()
        self.user1 = 7701
        self.user2 = 7702
        self.user3 = 7703
        
        # Reset user states
        update_user(self.user1, balance=100000, gems=50.0, level=10, xp=5000, guild_id=None)
        update_user(self.user2, balance=50000, gems=20.0, level=6, xp=2000, guild_id=None)
        update_user(self.user3, balance=1000, gems=0.0, level=2, xp=200, guild_id=None)

    def test_guild_creation(self):
        # User 3 lacks level and funds
        ok, msg, gdata = self.gm.create_guild(self.user3, "LOW", "Low Guild")
        self.assertFalse(ok)

        # User 1 has funds and level
        tag = f"T{uuid.uuid4().hex[:3]}".upper()
        ok, msg, gdata = self.gm.create_guild(self.user1, tag, f"Titan {tag}")
        self.assertTrue(ok)
        self.assertIsNotNone(gdata)

        guild = self.gm.get_guild(gdata["guild_id"])
        self.assertIsNotNone(guild)
        self.assertEqual(guild["tag"], tag)
        self.assertEqual(guild["leader_id"], self.user1)

    def test_guild_membership_and_treasury(self):
        creator_id = 7710
        update_user(creator_id, balance=100000, gems=50.0, level=10, xp=5000, guild_id=None)
        tag = f"K{uuid.uuid4().hex[:3]}".upper()
        ok, _, gdata = self.gm.create_guild(creator_id, tag, f"Knight {tag}")
        self.assertTrue(ok)
        gid = gdata["guild_id"]

        # User 2 joins guild
        ok, msg = self.gm.join_guild(self.user2, tag)
        self.assertTrue(ok)
        u2 = get_user(self.user2)
        self.assertEqual(u2.get("guild_id"), gid)

        # User 2 deposits 5000 coins
        ok, msg = self.gm.deposit_treasury(self.user2, 5000, currency="coins")
        self.assertTrue(ok)
        guild = self.gm.get_guild(gid)
        self.assertGreaterEqual(guild["treasury_coins"], 5000)

        # User 2 leaves guild
        ok, msg = self.gm.leave_guild(self.user2)
        self.assertTrue(ok)
        u2 = get_user(self.user2)
        self.assertIsNone(u2.get("guild_id"))

    def test_guild_rankings(self):
        top_guilds = self.gm.get_top_guilds(limit=5)
        self.assertIsInstance(top_guilds, list)

    def test_social_friend_system(self):
        f_u1 = 8801
        f_u2 = 8802
        update_user(f_u1, balance=1000, level=5)
        update_user(f_u2, balance=1000, level=5)

        # Send request
        ok, msg = self.sm.send_friend_request(f_u1, f_u2)
        self.assertTrue(ok)

        # Accept request
        ok, msg = self.sm.accept_friend_request(f_u2, f_u1)
        self.assertTrue(ok)

        friends1 = self.sm.get_friends(f_u1)
        friends2 = self.sm.get_friends(f_u2)
        f1_ids = [f["user_id"] for f in friends1]
        f2_ids = [f["user_id"] for f in friends2]
        self.assertIn(f_u2, f1_ids)
        self.assertIn(f_u1, f2_ids)

        # Remove friend
        ok, msg = self.sm.remove_friend(f_u1, f_u2)
        self.assertTrue(ok)

    def test_player_report(self):
        ok, msg = self.sm.submit_report(self.user1, self.user2, -1001234567, "Spamming offensive stickers")
        self.assertTrue(ok)
        self.assertIn("submitted", msg.lower())


if __name__ == "__main__":
    unittest.main()
