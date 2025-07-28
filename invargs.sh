#!/usr/bin/env bash
#
# progname
#   oneliner description
#
# invocation1: do something cool
# invocation2: do something not cool
#
# invocation1
#   more help text on invocation 1
#
# invocation2
#   more help text on invocation 2
#
# scott@smemsh.net
# https://github.com/smemsh/devskel/
# https://spdx.org/licenses/GPL-2.0
#

setenv  () { local v=$1; shift; IFS= eval $v="\$*"; }
setarr  () { local v=$1; shift; eval $v=\(\"\$@\"\); }
bomb    () { echo "${FUNCNAME[1]}: ${*}, aborting" >&2; false; exit; }
err     () { echo "${FUNCNAME[1]}: ${*}" >&2; }

flag    () { (((opts & $1) == $1)); }
flagstr () { flag $1 && printf true || printf false; }

# text comes from comment header at top of script
usage_until=invocation1:
usagex () { usage; false; exit; }
usage ()
{
	grep -B 999 -m 1 '^$' "$BASH_SOURCE"  | # until first blank
	grep -B 999 -m 1 "^..${usage_until}$" | # until stop record
	head -n -2 |	# but not the match
	tail -n +3 |	# or interpreter line
	cut -b 3-	# strip comment prefix
}

# works, but has blank line at the end despite my best efforts
usage ()
{
	sed -n -r '/^#\s'$startusage'$/,${/^#\s'$endusage'$/q;s/^..?//;p}' \
	$BASH_SOURCE
}

process_args ()
{
	local n
	opta=false
	optb=$((1<<n++))
	optc=$((1<<n++))
	optd=$((1<<n++))

	# 1/3 if using usagex()
	usagex () { for line in "${use[@]}"; do echo "$line"; done >&2; exit; }
	use=(
	"-a|--opta    description of opta option"
	"-a|--optb    description of optb option"
	"-a|--optc    description of optc option"
	"-a|--optd    description of optd option"
	"-h|--help    display help"
	)

	# 1/2
	eval set -- $(getopt -n "${0##*/}" \
		-o abcdh -l opta,optb,optc,optd,help -- "$@")
	# 2/2
	while true; do case $1 in
	(-a|--opta) opta=true; shift;;
	(-c|--optb) let "opts |= $optb"; shift;;
	(-d|--optc) let "opts |= $optc"; shift;;
	(-d|--optd) let "opts |= $optd"; shift;;
	(-h|--help) usagex;;
	(-H|--HELP) usage_exit;;
	(--) shift; break;;
	(*) echo "bad usage" >&2; false; return;;
	esac; done

	if ! (((opts & (opts - 1)) == 0))
	then echo "options [bcd] exclude each other" >&2; false; return; fi

	if ! ((opts)) # default
	then opts=$optb; fi
}

check_sanity ()
{
	true
}

main ()
{
	process_args "$@" || exit
	check_sanity || exit
	cd "$startdir" || exit

	if [[ $(declare -F $invname) ]]
	then $invname "$@"
	else echo "unimplemented command '$invname'" >&2; fi
}

startdir=$HOME
invname=${0##*/}
invdir=${0%/*}

# for wrappers with same name as wrapped, only works if not a symlink
savedpath=$PATH
cmdpath=${BASH_SOURCE%/*}
PATH=$(
	IFS=:
	newpath=($PATH)
	for ((i = 0; i < ${#newpath[@]}; i++))
	do if [[ ${newpath[i]} == "$cmdpath" ]]
	then unset 'newpath[i]'; break; fi; done
	printf "${newpath[*]}"
)
realexe=$(type -P $invname)
PATH=$savedpath
