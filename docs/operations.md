# Operation catalog

These operations are exposed through `canvas_read`. Use `canvas_describe_operation`
for exact path parameters, query filters, types, and usage notes. Every route is GET-only.
Canvas may deny individual features based on permissions or school configuration.

## Account Notifications

| Operation | Path |
| --- | --- |
| `account_notifications` | `/api/v1/accounts/{account_id}/account_notifications` |

## Announcements

| Operation | Path |
| --- | --- |
| `announcements` | `/api/v1/announcements` |

## Appointment Groups

| Operation | Path |
| --- | --- |
| `appointment_groups` | `/api/v1/appointment_groups` |
| `appointment_group` | `/api/v1/appointment_groups/{id}` |
| `next_appointment` | `/api/v1/appointment_groups/next_appointment` |

## Assignment Groups

| Operation | Path |
| --- | --- |
| `assignment_groups` | `/api/v1/courses/{course_id}/assignment_groups` |
| `assignment_group` | `/api/v1/courses/{course_id}/assignment_groups/{assignment_group_id}` |

## Assignments

| Operation | Path |
| --- | --- |
| `assignments` | `/api/v1/courses/{course_id}/assignments` |
| `assignment` | `/api/v1/courses/{course_id}/assignments/{id}` |
| `group_assignments` | `/api/v1/courses/{course_id}/assignment_groups/{assignment_group_id}/assignments` |
| `assignment_overrides` | `/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides` |
| `assignment_override` | `/api/v1/courses/{course_id}/assignments/{assignment_id}/overrides/{id}` |
| `assignment_group_members` | `/api/v1/courses/{course_id}/assignments/{assignment_id}/users/{user_id}/group_members` |

## Bookmarks

| Operation | Path |
| --- | --- |
| `bookmarks` | `/api/v1/users/self/bookmarks` |
| `bookmark` | `/api/v1/users/self/bookmarks/{id}` |

## Calendar Events

| Operation | Path |
| --- | --- |
| `calendar_events` | `/api/v1/calendar_events` |
| `calendar_event` | `/api/v1/calendar_events/{id}` |
| `course_timetable` | `/api/v1/courses/{course_id}/calendar_events/timetable` |

## Collaborations

| Operation | Path |
| --- | --- |
| `collaborations` | `/api/v1/courses/{course_id}/collaborations` |
| `group_collaborations` | `/api/v1/groups/{group_id}/collaborations` |

## Communication Channels

| Operation | Path |
| --- | --- |
| `communication_channels` | `/api/v1/users/{user_id}/communication_channels` |

## Conferences

| Operation | Path |
| --- | --- |
| `conferences` | `/api/v1/courses/{course_id}/conferences` |
| `group_conferences` | `/api/v1/groups/{group_id}/conferences` |

## Conversations

| Operation | Path |
| --- | --- |
| `conversations` | `/api/v1/conversations` |
| `conversation` | `/api/v1/conversations/{id}` |
| `unread_count` | `/api/v1/conversations/unread_count` |

## Courses

| Operation | Path |
| --- | --- |
| `courses` | `/api/v1/courses` |
| `course` | `/api/v1/courses/{id}` |
| `course_progress` | `/api/v1/courses/{course_id}/users/{user_id}/progress` |
| `course_users` | `/api/v1/courses/{course_id}/users` |
| `course_user` | `/api/v1/courses/{course_id}/users/{id}` |
| `course_activity` | `/api/v1/courses/{course_id}/activity_stream` |
| `course_activity_summary` | `/api/v1/courses/{course_id}/activity_stream/summary` |
| `course_todo` | `/api/v1/courses/{course_id}/todo` |
| `course_settings` | `/api/v1/courses/{course_id}/settings` |
| `course_permissions` | `/api/v1/courses/{course_id}/permissions` |

## Discussion Topics

| Operation | Path |
| --- | --- |
| `discussions` | `/api/v1/courses/{course_id}/discussion_topics` |
| `discussion` | `/api/v1/courses/{course_id}/discussion_topics/{topic_id}` |
| `discussion_view` | `/api/v1/courses/{course_id}/discussion_topics/{topic_id}/view` |
| `discussion_entries` | `/api/v1/courses/{course_id}/discussion_topics/{topic_id}/entries` |
| `discussion_replies` | `/api/v1/courses/{course_id}/discussion_topics/{topic_id}/entries/{entry_id}/replies` |
| `discussion_entry_list` | `/api/v1/courses/{course_id}/discussion_topics/{topic_id}/entry_list` |
| `group_discussions` | `/api/v1/groups/{group_id}/discussion_topics` |
| `group_discussion` | `/api/v1/groups/{group_id}/discussion_topics/{topic_id}` |
| `group_discussion_view` | `/api/v1/groups/{group_id}/discussion_topics/{topic_id}/view` |
| `group_discussion_entries` | `/api/v1/groups/{group_id}/discussion_topics/{topic_id}/entries` |
| `group_discussion_replies` | `/api/v1/groups/{group_id}/discussion_topics/{topic_id}/entries/{entry_id}/replies` |
| `group_discussion_entry_list` | `/api/v1/groups/{group_id}/discussion_topics/{topic_id}/entry_list` |

## Enrollments

| Operation | Path |
| --- | --- |
| `enrollments` | `/api/v1/users/{user_id}/enrollments` |
| `course_enrollments` | `/api/v1/courses/{course_id}/enrollments` |

## External Tools

| Operation | Path |
| --- | --- |
| `external_tools` | `/api/v1/courses/{course_id}/external_tools` |

## Favorites

| Operation | Path |
| --- | --- |
| `favorite_courses` | `/api/v1/users/self/favorites/courses` |
| `favorite_groups` | `/api/v1/users/self/favorites/groups` |

## Files

| Operation | Path |
| --- | --- |
| `files` | `/api/v1/courses/{course_id}/files` |
| `file` | `/api/v1/files/{id}` |
| `user_files` | `/api/v1/users/{user_id}/files` |
| `group_files` | `/api/v1/groups/{group_id}/files` |
| `folder_files` | `/api/v1/folders/{id}/files` |
| `folders` | `/api/v1/courses/{course_id}/folders` |
| `folder` | `/api/v1/folders/{id}` |
| `subfolders` | `/api/v1/folders/{id}/folders` |
| `user_folders` | `/api/v1/users/{user_id}/folders` |
| `group_folders` | `/api/v1/groups/{group_id}/folders` |

## Grading Periods

| Operation | Path |
| --- | --- |
| `grading_periods` | `/api/v1/courses/{course_id}/grading_periods` |
| `grading_period` | `/api/v1/courses/{course_id}/grading_periods/{id}` |

## Grading Standards

| Operation | Path |
| --- | --- |
| `grading_standards` | `/api/v1/courses/{course_id}/grading_standards` |
| `grading_standard` | `/api/v1/courses/{course_id}/grading_standards/{grading_standard_id}` |

## Group Categories

| Operation | Path |
| --- | --- |
| `group_categories` | `/api/v1/courses/{course_id}/group_categories` |
| `group_category` | `/api/v1/group_categories/{group_category_id}` |
| `category_groups` | `/api/v1/group_categories/{group_category_id}/groups` |

## Groups

| Operation | Path |
| --- | --- |
| `groups` | `/api/v1/users/self/groups` |
| `course_groups` | `/api/v1/courses/{course_id}/groups` |
| `group` | `/api/v1/groups/{group_id}` |
| `group_users` | `/api/v1/groups/{group_id}/users` |
| `group_memberships` | `/api/v1/groups/{group_id}/memberships` |
| `group_activity` | `/api/v1/groups/{group_id}/activity_stream` |
| `group_permissions` | `/api/v1/groups/{group_id}/permissions` |

## Late Policy

| Operation | Path |
| --- | --- |
| `late_policy` | `/api/v1/courses/{id}/late_policy` |

## Modules

| Operation | Path |
| --- | --- |
| `modules` | `/api/v1/courses/{course_id}/modules` |
| `module` | `/api/v1/courses/{course_id}/modules/{id}` |
| `module_items` | `/api/v1/courses/{course_id}/modules/{module_id}/items` |
| `module_item` | `/api/v1/courses/{course_id}/modules/{module_id}/items/{id}` |
| `module_item_sequence` | `/api/v1/courses/{course_id}/module_item_sequence` |

## New Quizzes

| Operation | Path |
| --- | --- |
| `new_quizzes` | `/api/quiz/v1/courses/{course_id}/quizzes` |
| `new_quiz` | `/api/quiz/v1/courses/{course_id}/quizzes/{assignment_id}` |

## Notification Preferences

| Operation | Path |
| --- | --- |
| `notification_preferences` | `/api/v1/users/{user_id}/communication_channels/{communication_channel_id}/notification_preferences` |

## Outcome Groups

| Operation | Path |
| --- | --- |
| `outcome_groups` | `/api/v1/courses/{course_id}/outcome_groups` |
| `outcome_group` | `/api/v1/courses/{course_id}/outcome_groups/{id}` |
| `outcome_group_outcomes` | `/api/v1/courses/{course_id}/outcome_groups/{id}/outcomes` |
| `outcome_subgroups` | `/api/v1/courses/{course_id}/outcome_groups/{id}/subgroups` |

## Outcome Results

| Operation | Path |
| --- | --- |
| `outcome_results` | `/api/v1/courses/{course_id}/outcome_results` |
| `outcome_rollups` | `/api/v1/courses/{course_id}/outcome_rollups` |

## Outcomes

| Operation | Path |
| --- | --- |
| `outcome` | `/api/v1/outcomes/{id}` |
| `outcome_alignments` | `/api/v1/courses/{course_id}/outcome_alignments` |

## Pages

| Operation | Path |
| --- | --- |
| `front_page` | `/api/v1/courses/{course_id}/front_page` |
| `pages` | `/api/v1/courses/{course_id}/pages` |
| `page` | `/api/v1/courses/{course_id}/pages/{url_or_id}` |
| `page_revisions` | `/api/v1/courses/{course_id}/pages/{url_or_id}/revisions` |
| `page_revision` | `/api/v1/courses/{course_id}/pages/{url_or_id}/revisions/{revision_id}` |
| `group_front_page` | `/api/v1/groups/{group_id}/front_page` |
| `group_pages` | `/api/v1/groups/{group_id}/pages` |
| `group_page` | `/api/v1/groups/{group_id}/pages/{url_or_id}` |

## Peer Reviews

| Operation | Path |
| --- | --- |
| `peer_reviews` | `/api/v1/courses/{course_id}/assignments/{assignment_id}/peer_reviews` |
| `submission_peer_reviews` | `/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}/peer_reviews` |

## Planner

| Operation | Path |
| --- | --- |
| `planner_items` | `/api/v1/planner/items` |
| `planner_notes` | `/api/v1/planner_notes` |
| `planner_note` | `/api/v1/planner_notes/{id}` |
| `planner_overrides` | `/api/v1/planner/overrides` |
| `planner_override` | `/api/v1/planner/overrides/{id}` |

## Quiz Questions

| Operation | Path |
| --- | --- |
| `quiz_questions` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions` |
| `quiz_question` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{id}` |

## Quiz Submission Questions

| Operation | Path |
| --- | --- |
| `quiz_submission_questions` | `/api/v1/quiz_submissions/{quiz_submission_id}/questions` |

## Quiz Submissions

| Operation | Path |
| --- | --- |
| `quiz_submissions` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/submissions` |
| `my_quiz_submission` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/submission` |
| `quiz_submission` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/submissions/{id}` |

## Quizzes

| Operation | Path |
| --- | --- |
| `quizzes` | `/api/v1/courses/{course_id}/quizzes` |
| `quiz` | `/api/v1/courses/{course_id}/quizzes/{id}` |

## Rubrics

| Operation | Path |
| --- | --- |
| `rubrics` | `/api/v1/courses/{course_id}/rubrics` |
| `rubric` | `/api/v1/courses/{course_id}/rubrics/{id}` |

## Search

| Operation | Path |
| --- | --- |
| `recipients` | `/api/v1/search/recipients` |

## Sections

| Operation | Path |
| --- | --- |
| `sections` | `/api/v1/courses/{course_id}/sections` |
| `section` | `/api/v1/sections/{id}` |
| `section_users` | `/api/v1/sections/{id}/users` |

## Smart Search

| Operation | Path |
| --- | --- |
| `smart_search` | `/api/v1/courses/{course_id}/smartsearch` |

## Submissions

| Operation | Path |
| --- | --- |
| `submission` | `/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}` |
| `student_submissions` | `/api/v1/courses/{course_id}/students/submissions` |
| `assignment_submissions` | `/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions` |

## Tabs

| Operation | Path |
| --- | --- |
| `tabs` | `/api/v1/courses/{course_id}/tabs` |
| `group_tabs` | `/api/v1/groups/{group_id}/tabs` |

## Users

| Operation | Path |
| --- | --- |
| `profile` | `/api/v1/users/{user_id}/profile` |
| `user` | `/api/v1/users/{id}` |
| `activity_stream` | `/api/v1/users/self/activity_stream` |
| `activity_summary` | `/api/v1/users/self/activity_stream/summary` |
| `todo` | `/api/v1/users/self/todo` |
| `todo_count` | `/api/v1/users/self/todo_item_count` |
| `upcoming_events` | `/api/v1/users/self/upcoming_events` |
| `missing_submissions` | `/api/v1/users/{user_id}/missing_submissions` |
| `graded_submissions` | `/api/v1/users/{id}/graded_submissions` |
| `course_nicknames` | `/api/v1/users/self/course_nicknames` |
| `user_colors` | `/api/v1/users/{id}/colors` |

