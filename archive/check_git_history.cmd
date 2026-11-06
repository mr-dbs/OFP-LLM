@echo off
rem check_git_history.cmd - 25 October: READ-ONLY. Shows where C:\dev\CWR came from, every branch and commit,
rem anything stashed or untracked, and whether any GR or Task Force work is already in the git history.
rem Writes C:\ofp-llm\logs\git_history.txt for Claude. It changes nothing.
setlocal
set "OUT=C:\ofp-llm\logs\git_history.txt"
cd /d C:\dev\CWR || (echo C:\dev\CWR not found.& pause & goto :eof)
> "%OUT%" echo ===== remotes
git remote -v >> "%OUT%" 2>&1
>>"%OUT%" echo ===== branches
git branch -a -vv >> "%OUT%" 2>&1
>>"%OUT%" echo ===== worktrees and stashes
git worktree list >> "%OUT%" 2>&1
git stash list >> "%OUT%" 2>&1
>>"%OUT%" echo ===== commits on any branch that the remote does not have (with files)
git log --all --not --remotes --stat --format="--- %%h %%ad %%an : %%s" --date=short >> "%OUT%" 2>&1
>>"%OUT%" echo ===== last 15 commits on main
git log -15 --format="%%h %%ad %%an : %%s" --date=short >> "%OUT%" 2>&1
>>"%OUT%" echo ===== commits that add or remove GR / Task Force markers
git log --all --format="%%h %%ad : %%s" --date=short -S"triGR" >> "%OUT%" 2>&1
git log --all --format="%%h %%ad : %%s" --date=short -S"dbsPatrolMove" >> "%OUT%" 2>&1
git log --all --format="%%h %%ad : %%s" --date=short -S"DBS GR" >> "%OUT%" 2>&1
git log --all --format="%%h %%ad : %%s" --date=short -i --grep="task force" --grep="taskforce" --grep="GR " --grep="chat" >> "%OUT%" 2>&1
>>"%OUT%" echo ===== every changed or untracked file
git status --porcelain --untracked-files=all >> "%OUT%" 2>&1
>>"%OUT%" echo ===== .gitignore
if exist .gitignore (type .gitignore >> "%OUT%") else (>>"%OUT%" echo none)
for %%f in ("%OUT%") do echo Written %%~ff (%%~zf bytes). Tell Claude.
pause
