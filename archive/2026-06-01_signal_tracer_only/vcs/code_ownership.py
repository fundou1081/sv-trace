"""
CodeOwnership - 代码所有权追踪
基于Git追踪每个文件/模块的负责人
"""
import os
import subprocess
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FileOwner:
    file: str
    owner: str
    last_modified: str
    commit_count: int = 0
    lines_added: int = 0
    lines_deleted: int = 0

class CodeOwnershipTracker:
    """代码所有权追踪器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
    
    def _run_git(self, args: List[str]) -> str:
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
    
    def get_file_owner(self, filepath: str) -> Optional[FileOwner]:
        """获取文件负责人"""
        # 使用git blame获取最后修改者
        output = self._run_git(['blame', '--line-porcelain', filepath])
        
        if not output or output.startswith('Error'):
            return None
        
        lines = output.split('\n')
        last_author = ""
        last_commit = ""
        
        for line in lines:
            if line.startswith('author '):
                last_author = line[7:].strip()
            elif line.startswith('author-time '):
                last_commit = line[12:].strip()
        
        # 获取统计信息
        stats = self._run_git(['log', '-1', '--pretty=format:%ai', '--', filepath])
        
        return FileOwner(
            file=filepath,
            owner=last_author,
            last_modified=stats or last_commit
        )
    
    def get_module_ownership(self, module: str) -> Dict[str, FileOwner]:
        """获取模块所有文件的所有权"""
        files = self._run_git(['ls-files', f'**/{module}*/**/*.sv'])
        
        ownership = {}
        for f in files.split('\n'):
            if f:
                owner = self.get_file_owner(f)
                if owner:
                    ownership[f] = owner
        
        return ownership
    
    def get_team_ownership(self) -> Dict[str, List[str]]:
        """获取团队成员负责的文件"""
        files = self._run_git(['ls-files', '**/*.sv']).split('\n')
        
        team_files = defaultdict(list)
        
        for f in files:
            if not f:
                continue
            owner = self.get_file_owner(f)
            if owner:
                team_files[owner.owner].append(f)
        
        return dict(team_files)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        team = self.get_team_ownership()
        
        total_files = sum(len(files) for files in team.values())
        total_lines = 0
        
        for files in team.values():
            for f in files:
                output = self._run_git(['log', '--oneline', '--numstat', '--', f])
                if output:
                    for line in output.split('\n'):
                        parts = line.split('\t')
                        if len(parts) >= 2 and parts[0] != '-':
                            try:
                                total_lines += int(parts[0])
                            except:
                                pass
        
        return {
            'total_files': total_files,
            'total_lines': total_lines,
            'team_size': len(team),
            'by_owner': {k: len(v) for k, v in team.items()}
        }
