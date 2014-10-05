#!/usr/bin/env bash
git checkout master
git remote update
ret=`git diff @{u}` # Diff the tracking branch
if [ -z "$ret" ]; then
    git checkout gh-pages
    exit
fi
git pull
tox -e testcoverage
git checkout gh-pages
rm -rf htmlcoverage
cp -r docs/build/htmlcoverage htmlcoverage
git add htmlcoverage/
git commit -m "Updated htmlcoverage" -a
git push origin gh-pages
rm -rf docs/build
git checkout gh-pages
