#!/usr/bin/env python

import sys

from launchpadlib.launchpad import Launchpad


def show_bp(bp, depends=False):
    global warning_count

    if bp.assignee:
        assignee = bp.assignee.name
    else:
        assignee = 'No assignee'

    if bp.milestone:
        milestone = bp.milestone.name
    else:
        milestone = 'No milestone'

    if depends:
        prefix = "  <-"
    else:
        warning_count += 1
        prefix = "*"


    print "%s %s (%s, %s, %s)\n%s %s" % (
        prefix,
        bp.name,
        bp.priority,
        assignee,
        milestone,
        " " * len(prefix),
        bp.web_link)

# Parse arguments
if len(sys.argv) < 3:
    print "Usage: %s PROJECT SERIES" % sys.argv[0]
    sys.exit(0)

projectname = sys.argv[1]
seriesname = sys.argv[2]
prio = ["Not", "Undefined", "Low", "Medium", "High", "Essential"]

# Log into LP
lp = Launchpad.login_anonymously('bp-issues', 'production', version='devel')

# Retrieve project, series and milestones
warning_count = 0
blueprints = []
project = lp.projects[projectname]
series = project.getSeries(name=seriesname)
future_milestones = []
current_milestone = None
for ms in series.active_milestones:
    next_milestone = current_milestone
    future_milestones.append(next_milestone)
    current_milestone = ms

implemented = under_review = in_progress = not_started = 0
next_count = 0
needs_assignee = []
needs_triage = []
unknown_status = []
depends_issues = []
already_implemented = []
extra_triage = []

for bp in series.valid_specifications:
    # Active milestone
    if bp.milestone == current_milestone:
        if bp.is_complete:
            if bp.implementation_status == 'Implemented':
                implemented += 1
            continue
        if prio.index(bp.priority) > 2:
            if bp.implementation_status == 'Needs Code Review':
                under_review += 1
            else:
                if bp.implementation_status in ('Unknown', 'Not started'):
                    not_started += 1
                else:
                    in_progress += 1

        # No assignee
        if not bp.assignee:
            needs_assignee.append(bp)

        # No priority
        if prio.index(bp.priority) < 2:
            needs_triage.append(bp)

        # Unknown status
        if bp.implementation_status == "Unknown":
            unknown_status.append(bp)

        # Dependencies
        for dep in bp.dependencies:
            if not dep.is_complete:
                if (prio.index(bp.priority) > prio.index(dep.priority) or not
                    dep.milestone):
                    depends_issues.append((bp, dep))

        continue

    if bp.milestone == next_milestone:
        # Next milestone count
        if prio.index(bp.priority) > 2:
            next_count += 1
        # Extra triage
        if bp.priority == 'Undefined':
            extra_triage.append(bp)

    if bp.milestone in future_milestones:
        # Early implementations
        if bp.implementation_status == 'Implemented':
            already_implemented.append(bp)

critical_bugs = []
open_critical = project.searchTasks(importance='Critical')
for bugtask in open_critical:
    if (bugtask.status != 'Fix Committed' and
        bugtask.milestone != current_milestone):
        critical_bugs.append(bugtask)

# Report
total = implemented + under_review + in_progress + not_started
print "Tracking %d blueprints for %s:" % (total, current_milestone.name)
print "%d%% done, %d%% under review, %d%% in progress, %d%% not started" % (
    int(implemented*100/total),
    int(under_review*100/total),
    int(in_progress*100/total),
    int(not_started*100/total))
print
if next_milestone:
    print "Next milestone currently has %d targeted blueprints" % next_count
    print

if needs_triage:
    print "Needs triaging:"
    for bp in needs_triage:
        show_bp(bp)
    print

if needs_assignee:
    print "Needs an assignee:"
    for bp in needs_assignee:
        show_bp(bp)
    print

if unknown_status:
    print "Needs a status update:"
    for bp in unknown_status:
        show_bp(bp)
    print

if depends_issues:
    print "Dependency issues:"
    for bp, dep in depends_issues:
        show_bp(bp)
        show_bp(dep, depends=True)
    print

if already_implemented:
    print "In a future milestone but already implemented:"
    for bp in already_implemented:
        show_bp(bp)
    print

if critical_bugs:
    print "Some critical bugs are not targeted to the current milestone:"
    for bugtask in critical_bugs:
        print "* %s" % bugtask.bug.web_link
        warning_count += 1
    print

if warning_count < 3 and extra_triage:
    print "You may consider triaging next milestone blueprints:"
    for bp in extra_triage:
        show_bp(bp)
    print
