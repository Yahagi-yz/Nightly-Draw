#!/usr/bin/env python3
"""Validate the current v0.1 card contract using only the standard library.

This is a project-specific validator, not a general JSON Schema engine.
Network availability and real publication rights require separate review.
"""
import argparse
import json
import logging
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'schema_version', 'id', 'title', 'category', 'content_nature', 'format',
    'region', 'language', 'body', 'reflection', 'editorial_note', 'sources',
    'images', 'review_status', 'release_status', 'related_tags'
}
ENUMS = {
    'category': {'world_story', 'person_story', 'historic_city'},
    'content_nature': {'fable_retelling', 'legend_retelling', 'literary_adaptation',
                       'historical_summary', 'original_fiction'},
    'format': {'text', 'image', 'mixed'},
    'review_status': {'draft', 'source_checked', 'editor_approved'},
    'release_status': {'sample_only', 'unpublished', 'published'},
}
SOURCE_KEYS = {'title', 'publisher', 'url', 'accessed_on', 'supports', 'reuse_note'}
IMAGE_KEYS = {'url', 'alt', 'kind', 'source_url', 'creator', 'rights_status', 'rights_note'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def https_url(value):
    if not isinstance(value, str):
        return False
    try:
        parts = urlparse(value)
        return parts.scheme == 'https' and bool(parts.hostname) and not parts.username and not parts.password
    except ValueError:
        return False


def validate_card(card):
    require(isinstance(card, dict), '卡片必须是对象')
    require(set(card) == REQUIRED, '卡片字段缺失或包含未定义字段')
    require(card['schema_version'] == '0.1.0', '不支持的数据版本')
    require(isinstance(card['id'], str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', card['id']), 'ID格式错误')
    for field in ('title', 'region', 'body', 'editorial_note'):
        require(nonempty(card[field]), field + '不能为空')
    require(isinstance(card['reflection'], str), 'reflection必须是字符串')
    require(card['language'] == 'zh-CN', '样卡语言必须是zh-CN')
    for field, allowed in ENUMS.items():
        require(isinstance(card[field], str) and card[field] in allowed, field + '的值无效')
    require(isinstance(card['sources'], list), 'sources必须是数组')
    if card['content_nature'] != 'original_fiction':
        require(bool(card['sources']), '非原创题材缺少来源')
    for source in card['sources']:
        require(isinstance(source, dict) and set(source) == SOURCE_KEYS, '来源字段错误')
        require(all(nonempty(v) for v in source.values()), '来源字段不能为空')
        require(https_url(source['url']), '来源必须是有效的HTTPS地址，不得含凭据')
        try:
            parsed_date = date.fromisoformat(source['accessed_on'])
        except ValueError as exc:
            raise ValueError('来源访问日期无效') from exc
        require(parsed_date.isoformat() == source['accessed_on'], '日期必须使用YYYY-MM-DD格式')
    images = card['images']
    require(isinstance(images, list) and len(images) <= 3, 'images必须是最多3项的数组')
    if card['format'] in ('image', 'mixed'):
        require(bool(images), '图片/图文卡必须有实际图片')
    for image in images:
        require(isinstance(image, dict) and set(image) == IMAGE_KEYS, '图片字段错误')
        require(all(nonempty(v) for v in image.values()), '图片字段不能为空')
        require(https_url(image['url']) and https_url(image['source_url']), '图片及出处地址无效')
        require(image['kind'] in ('photograph', 'artwork', 'generated_illustration'), '图片性质无效')
        require(image['rights_status'] in ('verified', 'pending'), '图片权利状态无效')
        if card['format'] in ('image', 'mixed') or card['release_status'] == 'published':
            require(image['rights_status'] == 'verified', '图片权利未核验，不能作为正式展示图片')
    require(isinstance(card['related_tags'], list), '关联标签必须是数组')
    require(all(nonempty(tag) for tag in card['related_tags']), '关联标签无效')
    require(len(card['related_tags']) == len(set(card['related_tags'])), '关联标签重复')
    if card['release_status'] == 'published':
        require(card['review_status'] == 'editor_approved', '正式发布前必须通过编辑审核')


def validate_project(root):
    root = Path(root)
    paths = sorted((root / 'content/cards').glob('*.json'))
    require(bool(paths), '未找到卡片文件')
    seen = set()
    for path in paths:
        card = json.loads(path.read_text(encoding='utf-8'))
        validate_card(card)
        require(card['id'] not in seen, '卡片ID重复：' + card['id'])
        seen.add(card['id'])
        logging.info('卡片结构通过：%s', path.name)
    schedule = json.loads((root / 'config/schedule.json').read_text(encoding='utf-8'))
    require(schedule['timezone'] == 'Asia/Shanghai', '时区偏离北京时间')
    require(schedule['local_time'] == '22:00', '时间偏离用户指定的22:00')
    require(schedule['frequency'] == 'daily', '频率必须为每日')
    require(schedule['utc_cron_reference'] == '0 14 * * *', 'UTC时间换算错误')
    require(type(schedule['enabled']) is bool, 'enabled必须为布尔值')
    if schedule['enabled']:
        require(nonempty(schedule.get('task_id')), '开启状态必须有真实任务ID')
        require(nonempty(schedule.get('provider')), '开启状态必须说明服务提供方')
        require(schedule.get('provider_status') == 'active', '开启状态必须对应active')
    else:
        require(schedule.get('provider_status') != 'active', '未开启却标记active')
    logging.info('共%s张卡片；这是结构验证，不代表联网、版权或推送验收。', len(paths))
    return len(paths)


def main():
    parser = argparse.ArgumentParser(description='校验每日抽卡样例数据，不联网、不推送。')
    parser.add_argument('--root', type=Path, default=ROOT, help='项目根目录')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    try:
        validate_project(args.root)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        logging.error('校验失败：%s', exc)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
