#!/bin/sh
# play.sh FRAMES -> runs bot, prints score digits + state every 60 frames
N=${1:-3600}
printf "run 60\nrun 2 X\nrun 10\nwatch @score 8\nauto $N @ballx @bally @bst\n" | ./run.py > /tmp/p_score.txt
printf "run 60\nrun 2 X\nrun 10\nwatch @mult 3\nauto $N @ballx @bally @bst\n" | ./run.py > /tmp/p_a.txt
printf "run 60\nrun 2 X\nrun 10\nwatch @boss_stage 4\nauto $N @ballx @bally @bst\n" | ./run.py > /tmp/p_b.txt
printf "run 60\nrun 2 X\nrun 10\nwatch @emp_lvl 1\nauto $N @ballx @bally @bst\n" | ./run.py > /tmp/p_c.txt
printf "run 60\nrun 2 X\nrun 10\nwatch @multiball 1\nauto $N @ballx @bally @bst\n" | ./run.py > /tmp/p_d.txt
paste /tmp/p_score.txt /tmp/p_a.txt /tmp/p_b.txt /tmp/p_c.txt /tmp/p_d.txt | grep "^f" | awk '{s=""; for(i=2;i<=9;i++) s=s $i; printf "%s score=%s mult=%s balls=%s | stage=%s eyes=%s awake=%s | emp=%s mb=%s\n",$1,s,$11,$13,$15,$17,$18,$20,$22}'
