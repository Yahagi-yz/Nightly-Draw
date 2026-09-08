#!/usr/bin/env python3
"""Create a new PRIVATE GitHub repo only when explicitly invoked with --apply.

Uses the user's existing GitHub CLI login; does not request, print or store tokens.
Does not overwrite existing repositories or create scheduled tasks.
"""
import argparse
import logging
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = 'Yahagi-yz/Nightly-Draw'
FILES = ['README.md', 'MISSION.md', 'CONTEXT.md', 'ROADMAP.md', 'AGENTS.md',
         'NOTICE.md', '.gitignore', 'preview.html', 'docs', 'config', 'prompts',
         'schemas', 'content', 'scripts', 'tests', 'issues']


def run(args, check=True):
    result = subprocess.run(args, cwd=str(ROOT), text=True, encoding='utf-8',
                            errors='replace', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        # Avoid echoing external diagnostics that could accidentally contain sensitive values.
        raise RuntimeError('命令未成功（退出码%s）：%s；请在本机检查登录、权限及网络。' %
                           (result.returncode, args[0] + ' ' + args[1]))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='每日抽卡建仓：默认仅预演，--apply才实际创建私有仓库并上传。')
    parser.add_argument('--repo', default=DEFAULT_REPO, help='owner/repo；owner须与本机GitHub登录一致')
    parser.add_argument('--apply', action='store_true', help='实际初始化Git并创建、上传全新私有仓库')
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9_.-]*', args.repo):
        parser.error('--repo必须为合法的owner/repo格式')
    if not args.apply:
        print('仅预演：未联网、未建仓、未推送。')
        print('拟创建私有仓库：' + args.repo)
        print('上传目录：' + str(ROOT))
        print('不创建定时任务；执行需另加 --apply。')
        return 0
    try:
        for binary in ('git', 'gh'):
            if shutil.which(binary) is None:
                raise RuntimeError('本机未安装' + binary + '，未执行建仓。')
        # Refuse to alter either an existing checkout or a parent repository.
        if (ROOT / '.git').exists() or run(['git', 'rev-parse', '--show-toplevel'], check=False).returncode == 0:
            raise RuntimeError('目录已在Git仓库中；为避免误改，脚本停止。请使用独立解压目录。')
        run(['gh', 'auth', 'status', '--hostname', 'github.com'])
        login = run(['gh', 'api', '--hostname', 'github.com', 'user', '--jq', '.login']).stdout.strip()
        if login.lower() != args.repo.split('/')[0].lower():
            raise RuntimeError('本机GitHub登录与目标owner不同，未执行建仓。')
        for field in ('user.name', 'user.email'):
            if not run(['git', 'config', '--get', field], check=False).stdout.strip():
                raise RuntimeError('请先在本机配置Git的' + field + '，未执行建仓。')
        exists = run(['gh', 'repo', 'view', args.repo, '--json', 'nameWithOwner'], check=False)
        if exists.returncode == 0:
            raise RuntimeError('目标仓库已存在；不会覆盖或追加上传。')
        for item in FILES:
            if not (ROOT / item).exists():
                raise RuntimeError('初始化包缺少文件：' + item)
        # Local validation before any mutation.
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        from validate import validate_project
        validate_project(ROOT)
        run(['git', 'init'])
        run(['git', 'symbolic-ref', 'HEAD', 'refs/heads/main'])
        run(['git', 'add', '--'] + FILES)
        run(['git', 'commit', '-m', 'docs: initialize nightly draw product foundation'])
        run(['gh', 'repo', 'create', args.repo, '--private', '--source', str(ROOT),
             '--remote', 'origin', '--push', '--disable-wiki', '--description',
             '每日睡前抽卡：世界故事、人物经历与历史名城；未来App项目。'])
        # Verify remote identity after the write. This does not verify notification delivery.
        verified = run(['gh', 'repo', 'view', args.repo, '--json', 'nameWithOwner,isPrivate,url']).stdout.strip()
        logging.info('建仓及上传命令完成；请核对返回的仓库信息：%s', verified)
        logging.info('定时推送仍未创建。CONTEXT.md中的交付时状态是历史快照，请基于真实结果另行更新。')
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        logging.error('%s', exc)
        logging.error('未报告成功；如已创建本地.git或远端仓库，脚本不会自动删除，请先核对实际状态。')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
