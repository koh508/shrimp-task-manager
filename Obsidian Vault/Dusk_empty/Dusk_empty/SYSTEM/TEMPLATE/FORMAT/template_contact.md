---
company:
location:
title:
email:
phone: 0
aliases:
tags:
type: contact
---
# Personal Notes


````tabs
tab: Scheduled Meetings
```dataview
TABLE scheduled_date as "Scheduled Date", start_time as "Start Time", summary as "Summary"
from #contact/template_area_note_sub
where contains(type,"meeting")
sort meeting_status asc, scheduled_date asc
```
````
````tabs
tab: Ongoing Tasks

```tasks
not done
tags include #contact/template_area_note_sub
path does not include SYSTEM
sort by due date
```
````
````tabs
tab: Completed Tasks
```tasks
done
tags include #contact/template_area_note_sub
path does not include SYSTEM
sort by due date
```
````
