python --version
coverage --version
coverage run tests/t_all_tests.py $@
if [ -z $1 ]; then
    coverage report -m --omit=tests/*
fi
