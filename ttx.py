#!/usr/bin/env python

import sys

from launchpadlib.launchpad import Launchpad


def show_bp(bp, issues):
    if issues:
        msg = "%s (%s" % (bp.name, bp.priority)
        if bp.assignee:
            msg = "%s, %s" % (msg, bp.assignee.name)
        if bp.milestone:
            msg = "%s, %s" % (msg, bp.milestone.name)
        print "%s)\n%s\n%s" % (msg, bp.web_link, issues)


# Parse arguments
if len(sys.argv) < 3:
    print "Usage: %s PROJECT SERIES" % sys.argv[0]
    sys.exit(0)

projectname = sys.argv[1]
seriesname = sys.argv[2]
prio = ["Not", "Undefined", "Low", "Medium", "High", "Essential"]

# Log into LP
lp = Launchpad.login_anonymously('bp-issues', 'production', version='devel')

# Retrieve project, series and corresponding blueprints
blueprints = []
project = lp.projects[projectname]
series = project.getSeries(name=seriesname)
for bp in series.valid_specifications:
    if not bp.is_complete:
        blueprints.append(bp)

# Get the milestones for the series
milestones = []
for ms in series.active_milestones_collection:
    milestones.append(ms)

# Find targeted blueprints that are not in the series
for bp in project.valid_specifications:
    if bp.milestone in milestones:
        if bp not in blueprints:
            show_bp(bp,
                "* Not in series goal while targeted to a series milestone\n")

for bp in blueprints:
    issues = ""
    # No assignee
    if bp.milestone:
        if not bp.assignee:
            issues += "* Targeted to a milestone but has no assignee\n"
        if bp.implementation_status == "Unknown":
            issues += "* Targeted to a milestone but unknown status\n"

    # No priority
    if prio.index(bp.priority) < 2:
        issues += "* No priority\n"

    # Essential and no target
    if bp.priority == "Essential" and not bp.milestone:
        issues += "* Essential but not targeted to a milestone\n"

    # Dependencies
    for dep in bp.dependencies:
        if not dep.is_complete:
            if dep not in blueprints and dep.target == project:
                issues += "* Depends on blueprint that is not in plan"
                issues += " (%s)\n" % dep.name
            if prio.index(bp.priority) > prio.index(dep.priority):
                issues += "* Depends on blueprint with lower priority"
                issues += " (%s)\n" % dep.name

    show_bp(bp, issues)
