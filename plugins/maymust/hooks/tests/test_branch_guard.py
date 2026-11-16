import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


HOOK = Path(__file__).resolve().parents[1] / "branch-guard.sh"
ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
           GIT_AUTHOR_NAME="test", GIT_AUTHOR_EMAIL="test@example.com",
           GIT_COMMITTER_NAME="test", GIT_COMMITTER_EMAIL="test@example.com")


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True)


class BranchGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="branch guard ")
        cls.root = Path(cls.tmp.name).resolve()
        cls.dev = cls.root / "main checkout"
        cls.feature = cls.root / "feature"
        cls.detached = cls.root / "detached"
        cls.dev.mkdir()
        git(cls.dev, "init", "-q", "-b", "dev")
        git(cls.dev, "commit", "-q", "--allow-empty", "-m", "init")
        git(cls.dev, "worktree", "add", "-q", "-b", "feat/x", str(cls.feature))
        git(cls.dev, "worktree", "add", "-q", "--detach", str(cls.detached))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def decide(self, cwd, tool_input):
        payload = json.dumps({"cwd": str(cwd), "tool_input": tool_input})
        result = subprocess.run(["bash", str(HOOK)], input=payload, cwd=self.root, env=ENV,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return "pass"
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]

    def test_decision_follows_the_folder_where_each_commit_runs(self):
        dev, feature = shlex.quote(str(self.dev)), shlex.quote(str(self.feature))
        cases = [
            ("cd 로 feature 워크트리에 들어가 커밋", self.dev,
             {"command": f"cd {feature} && git commit -m test"}, "pass"),
            ("git -C 로 feature 워크트리에 커밋", self.dev,
             {"command": f"git -C {feature} commit -m test"}, "pass"),
            ("feature 에서 git -C 로 dev 체크아웃에 커밋", self.feature,
             {"command": f"git -C {dev} commit -m test"}, "ask"),
            ("dev 에서 커밋", self.dev, {"command": "git commit -m test"}, "ask"),
            ("feature 에서 dev 체크아웃으로 cd 후 커밋", self.feature,
             {"command": f"cd {dev} && git commit -m test"}, "ask"),
            ("Codex workdir 가 feature", self.dev,
             {"command": "git commit -m test", "workdir": str(self.feature)}, "pass"),
            ("detached HEAD 에서 커밋", self.detached, {"command": "git commit -m test"}, "pass"),
            ("git status", self.dev, {"command": "git status"}, "pass"),
            ("git commit-tree", self.dev, {"command": "git commit-tree HEAD^{tree} -m test"}, "pass"),
            ("커밋 여럿 중 하나가 dev", self.dev,
             {"command": f"cd ../feature && git commit -m one; cd {dev} && git commit -m two"}, "ask"),
            ("상대 경로 cd 후 커밋", self.dev, {"command": "cd ../feature && git commit -m test"}, "pass"),
            ("git 전역 옵션 뒤의 commit", self.dev,
             {"command": "git -c user.name=x --no-pager commit -m test"}, "ask"),
            ("줄바꿈으로 나뉜 cd 와 커밋", self.dev, {"command": f"cd {feature}\ngit commit -m test"}, "pass"),
            ("서브셸 안의 cd 는 밖으로 이어지지 않음", self.dev,
             {"command": f"(cd {feature}) && git commit -m test"}, "ask"),
            ("커밋 출력을 파이프로 넘김", self.dev,
             {"command": f"cd {feature} && git commit -m test | tail -1"}, "pass"),
            ("파이프 안의 cd 는 이어지지 않음", self.dev,
             {"command": f"cd {feature} | cat; git commit -m test"}, "ask"),
            ("백그라운드 cd 는 이어지지 않음", self.dev,
             {"command": f"cd {feature} & wait; git commit -m test"}, "ask"),
            ("값을 받는 전역 옵션 --attr-source", self.dev,
             {"command": "git --attr-source HEAD commit -m test"}, "ask"),
            ("--work-tree 지정은 뒤따르는 -C 와 함께여도 통과", self.feature,
             {"command": f"git --work-tree {feature} -C {dev} commit -m test"}, "pass"),
            ("변수 전개로 경로를 확인할 수 없음", self.dev,
             {"command": 'cd "$WORKTREE" && git commit -m test'}, "pass"),
            ("git 저장소가 아닌 폴더", self.root, {"command": "git commit -m test"}, "pass"),
            ("bash -c 안의 커밋", self.feature, {"command": f'bash -lc "cd {dev} && git commit -m test"'}, "ask"),
            ("Codex cmd 와 workdir 가 dev", self.feature,
             {"cmd": "git commit -m test", "workdir": str(self.dev)}, "ask"),
            ("Codex 배열 명령", self.feature,
             {"command": ["bash", "-lc", "git commit -m test"], "workdir": str(self.dev)}, "ask"),
        ]
        for label, cwd, tool_input, expected in cases:
            with self.subTest(label):
                self.assertEqual(self.decide(cwd, tool_input), expected)

    def test_ask_names_the_protected_folder_and_branch(self):
        payload = json.dumps({"cwd": str(self.feature),
                              "tool_input": {"command": f"git -C {shlex.quote(str(self.dev))} commit -m test"}})
        result = subprocess.run(["bash", str(HOOK)], input=payload, env=ENV,
                                capture_output=True, text=True, timeout=10)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertIn(str(self.dev), output["permissionDecisionReason"])
        self.assertIn("dev", output["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
