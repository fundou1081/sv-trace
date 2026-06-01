"""
VCSManager - Git工作流管理器
集成Git操作，追踪版本、变更、代码所有权
"""
import os
import subprocess
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CommitInfo:
    commit: str
    message: str
    author: str
    date: str
    files: List[str]

class VCSManager:
    """Git工作流管理器"""
    
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
    
    def get_file_history(self, filepath: str, limit: int = 20) -> List[CommitInfo]:
        """获取文件历史"""
        output = self._run_git(['log', '--oneline', f'--limit={limit}', '--', filepath])
        if not output or output.startswith('Error'):
            return []
        
        commits = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split(' ', 1)
            if len(parts) == 2:
                commits.append(CommitInfo(
                    commit=parts[0],
                    message=parts[1],
                    author="",
                    date="",
                    files=[filepath]
                ))
        
        return commits
    
    def find_changed_files(self, since: str, until: str = "HEAD") -> List[str]:
        """找出两个版本间变更的文件"""
        output = self._run_git(['diff', '--name-only', since, until])
        if not output:
            return []
        return output.split('\n')
    
    def blame_file(self, filepath: str) -> Dict[str, int]:
        """获取文件每行的作者"""
        output = self._run_git(['blame', '--line-porcelain', filepath])
        if not output or output.startswith('Error'):
            return {}
        
        lines = output.split('\n')
        author_lines = {}
        current_author = ""
        
        for line in lines:
            if line.startswith('author '):
                current_author = line[7:].strip()
            elif line.startswith('author-mail'):
                pass  # 忽略
            elif line and line[0].isdigit():
                if current_author:
                    author_lines[current_author] = author_lines.get(current_author, 0) + 1
        
        return author_lines
    
    def get_branch_status(self) -> Dict:
        """获取分支状态"""
        branch = self._run_git(['branch', '--show-current'])
        status = self._run_git(['status', '--porcelain'])
        
        ahead = 0
        behind = 0
        if '/' in branch:
            remote_branch = self._run_git(['rev-parse', '--abbrev-ref', f'{branch}@{{upstream}}'])
            if remote_branch:
                ahead = len(self._run_git(['log', f'{branch}..{remote_branch}', '--oneline']).split('\n'))
                behind = len(self._run_git(['log', f'{remote_branch}..{branch}', '--oneline']).split('\n'))
        
        return {
            'branch': branch,
            'ahead': ahead,
            'behind': behind,
            'has_changes': len(status) > 0,
            'status': status
        }
    
    def create_branch(self, branch_name: str, start_point: str = "HEAD") -> bool:
        """创建分支"""
        result = self._run_git(['checkout', '-b', branch_name, start_point])
        return not result.startswith('Error')
    
    def merge_branch(self, source: str, target: str = "HEAD") -> Dict:
        """合并分支"""
        # 先切换到target
        self._run_git(['checkout', target])
        
        # 执行merge
        result = self._run_git(['merge', source])
        
        return {
            'success': not result.startswith('Error'),
            'output': result,
            'conflicts': 'CONFLICT' in result if result else False
        }
