from pathlib import Path
import subprocess,tarfile,shutil,json
root=Path.cwd();dest=root/'build/icon-release-20261027';dest.mkdir(parents=True,exist_ok=False)
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
p=subprocess.Popen(['git','archive','--format=tar',commit,'game','tools/export_builds.py'],stdout=subprocess.PIPE)
with tarfile.open(fileobj=p.stdout,mode='r|') as archive:
    archive.extractall(dest,filter='data')
if p.wait(): raise SystemExit('git archive failed')
for name in ['export_presets.cfg','assets/characters/roles/blood_ranger_bow.res']:
    f=dest/'game'/name;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/'game'/name,f)
cache=root/'game/.godot/imported'
if cache.is_dir():shutil.copytree(cache,dest/'game/.godot/imported')
for name in ['global_script_class_cache.cfg','uid_cache.bin']:
    f=root/'game/.godot'/name
    if f.exists():shutil.copy2(f,dest/'game/.godot'/name)
(root/'output/official-icons-20261027/release-source.json').write_text(json.dumps({'commit':commit,'path':str(dest),'source':'git archive HEAD game tools/export_builds.py','local_build_inputs':['export_presets.cfg','blood_ranger_bow.res'],'unrelated_working_tree_changes':'excluded'},indent=2))
print('Release source ready:',dest,commit,flush=True)
