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

isset   () { ((opts & $1)); } # tmpl isset

# tmpl errexit
set -e
trap_err () { echo "$FUNCNAME: code $1, line: $2, cmd: \"$3\""; exit $1; }
trap 'trap_err $? $LINENO "$BASH_COMMAND"' ERR

# tmpl tmpdir
tmpdir=`mktemp -d`
chmod 0755 $tmpdir
trap_exit () { (($1 == 0)) && rm -rf ${tmpdir:?}; }
trap 'trap_exit $?' EXIT

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
	# tmpl isset
	local n
	optb=$((1<<n++))

	# 1/3 if tmpl _usagex()
	use=(
	"-b|--opta description of optb via raw variable"
	"-a|--optb description of opta via isset accessor" # tmpl isset
	"-c [n] | --optc [n] description of optc with optional arg"
	"-d <arg> | --optd <arg> description of optd with mandatory arg"
	"-h|--help display help"
	)
	usagex () { _usagex "${use[@]}"; }
	_usagex() { local a; for a; do err "$a"; done; false; exit; }

	# 1/2
	eval set -- $(getopt -n $invname \
	-o habc::d: \
	-l help,flaga,optb,optc::,optd: \
	-- "$@")

	# 2/2
	while true; do case $1 in
	(-a|--optflag_a) let opta++; shift;;
	(-b|--optflag_b) let "opts |= $optb"; shift;;
	(-c|--optarg_c) shift; optc="${1:-default_value}"; shift;;
	(-d|--optarg_d) shift; optd="${1}"; shift;;
	(-h|--help) usage; exit;;
	(-h|--help) cat <<- %
		help text
		%
		bomb "read script for more usage";;
	(--) shift; break;;
	(*) usagex;;
	esac; done

	# tmpl isset
	isset $optflag_a && isset $optflag_b &&
		bomb "flags b and d are mutually exclusive"

	args=("$@")
}

check_sanity ()
{
	true
}

main ()
{
	process_args "$@" || exit
	check_sanity || exit
	cd "${startdir:-$HOME}" || exit # tmpl startdir

	if [[ $(declare -F $invname) ]]
	then $invname "${args[@]}"
	else bomb "unimplemented command '$invname'"; fi
}

invname=${0##*/} # 0.9.0
invdir=${0%/*}

main "$@"
