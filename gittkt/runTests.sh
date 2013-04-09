coverage run tests/t_all_tests.py $1
if [ -z $1 ]; then
    coverage report -m --omit=tests/*
fi
