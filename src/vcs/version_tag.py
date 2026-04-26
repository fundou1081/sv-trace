"""
VersionTag - 版本标签系统
基于Git的版本标签管理，支持版本血缘追踪
"""
import os
import subprocess
import json
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class VersionTag:
    """版本标签"""
    name: str
    version: str
    commit: str
    message: str
    author: str
    timestamp: str
    tags: List[str] = field(default_factory=list)
    parent_tags: List[str] = field(default_factory=list)

class VersionTagManager:
    """版本标签管理器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
    
    def _run_git(self, args: List[str]) -> str:
        """执行git命令"""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {e}"
    
    def create_tag(self, version: str, message: str = "", 
                   tags: List[str] = None, parent_tag: str = None) -> bool:
        """创建版本标签"""
        tag_name = f"v{version}"
        
        # 检查是否已存在
        if self._run_git(['tag', '-l', tag_name]):
            return False
        
        # 创建标签
        if message:
            self._run_git(['tag', '-a', tag_name, '-m', message])
        else:
            self._run_git(['tag', tag_name])
        
        # 添加额外标签
        if tags:
            for tag in tags:
                self._run_git(['tag', '-a', tag, '-m', f"{tag_name}: {tag}"])
        
        # 记录父标签
        if parent_tag:
            parent_file = os.path.join(self.repo_path, '.git', 'tag_parents')
            with open(parent_file, 'a') as f:
                f.write(f"{tag_name}->{parent_tag}\n")
        
        return True
    
    def list_tags(self, pattern: str = "*") -> List[VersionTag]:
        """列出标签"""
        output = self._run_git(['tag', '-l', '--format=%(refname:short)|%(objectname:short)|%(subject)|%(authorname)|%(creatordate:iso)'])
        
        if not output or output.startswith('Error'):
            return []
        
        tags = []
        for line in output.split('\n'):
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) >= 5:
                tag_name = parts[0]
                commit = parts[1]
                message = parts[2]
                author = parts[3]
                timestamp = parts[4]
                
                tags.append(VersionTag(
                    name=tag_name,
                    version=tag_name.lstrip('v'),
                    commit=commit,
                    message=message,
                    author=author,
                    timestamp=timestamp
                ))
        
        return tags
    
    def get_tag_info(self, tag_name: str) -> Optional[VersionTag]:
        """获取标签详情"""
        tags = self.list_tags(tag_name)
        for tag in tags:
            if tag.name == tag_name.lstrip('v'):
                # 加载额外信息
                tag_file = os.path.join(self.repo_path, '.git', f'tag_{tag.name}')
                if os.path.exists(tag_file):
                    with open(tag_file, 'r') as f:
                        data = json.load(f)
                        tag.tags = data.get('tags', [])
                        tag.parent_tags = data.get('parent_tags', [])
                return tag
        return None
    
    def get_lineage(self, tag_name: str) -> List[str]:
        """获取版本血缘链"""
        lineage = [tag_name]
        parent_file = os.path.join(self.repo_path, '.git', 'tag_parents')
        
        if not os.path.exists(parent_file):
            return lineage
        
        with open(parent_file, 'r') as f:
            for line in f:
                if line.startswith(f"{tag_name}->"):
                    parent = line.split('->')[1].strip()
                    lineage.extend(self.get_lineage(parent))
        
        return lineage
    
    def checkout_tag(self, tag_name: str) -> bool:
        """切换到指定标签"""
        result = self._run_git(['checkout', tag_name])
        return not result.startswith('Error')
    
    def diff_tags(self, tag1: str, tag2: str) -> Dict:
        """对比两个版本的差异"""
        # 获取commit范围
        commit1 = self._run_git(['rev-list', '-1', tag1])
        commit2 = self._run_git(['rev-list', '-1', tag2])
        
        # 获取变更文件
        diff = self._run_git(['diff', '--stat', f"{tag1}..{tag2}"])
        
        # 获取日志
        log = self._run_git(['log', '--oneline', f"{tag1}..{tag2}"])
        
        return {
            'tag1': tag1,
            'tag2': tag2,
            'commit1': commit1,
            'commit2': commit2,
            'diff': diff,
            'commits': log.split('\n') if log else []
        }
    
    def export_tags(self, filepath: str) -> bool:
        """导出标签数据"""
        tags = self.list_tags()
        data = {
            'export_time': datetime.now().isoformat(),
            'tags': [t.__dict__ for t in tags]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    
    def get_latest_tag(self) -> Optional[str]:
        """获取最新标签"""
        tags = self.list_tags()
        if not tags:
            return None
        
        # 按时间排序
        sorted_tags = sorted(tags, key=lambda t: t.timestamp, reverse=True)
        return sorted_tags[0].name
