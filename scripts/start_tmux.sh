#!/bin/sh
#
# Setup a work space called `work` with two windows
# first window has 3 panes.
# The first pane set at 65%, split horizontally, set to api root and running vim
# pane 2 is split at 25% and running redis-server
# pane 3 is set to api root and bash prompt.
# note: `api` aliased to `cd ~/path/to/work`
#
session="work"

tmux start-server

tmux has-session -t $session 2>/dev/null

if [ $? != 0 ]; then
    tmux new-session -d -s $session -n Main

    tmux splitw -h
    tmux send-keys "nvim" C-m

    tmux selectp -t 0

    tmux new-window -t $session:1 -n WoTo

    tmux selectp -t 1
    tmux send-keys "woto" C-m

    tmux splitw -h
    tmux send-keys "nvim" C-m

    tmux selectp -t 0

    # return to main vim window
    tmux select-window -t $session:0

    # Finished setup, attach to the tmux session!
    tmux attach-session -t $session
fi

tmux attach-session -t $session
