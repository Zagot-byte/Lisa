#!/usr/bin/env fish
# Lisa stderr hook for Fish shell
# Add to ~/.config/fish/conf.d/lisa.fish

function _lisa_hook --on-event fish_postexec
    set last_status $status
    set last_cmd $argv[1]

    # only trigger on failure, skip lisa itself
    if test $last_status -ne 0; and not string match -q 'lisa*' $last_cmd
        lisa --stderr "Command '$last_cmd' failed with exit code $last_status"
    end
end
