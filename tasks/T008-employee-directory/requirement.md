An internal company app. Each employee has one row in `employees`, linked to their login by `user_id`. Employees in the department `HR` handle pay.

R1. Provide a view `public.employee_directory` with exactly the columns `id`, `full_name` and `department`. Every signed-in user who is an employee can see every employee in it. Signed-in users who are not employees see no rows in it.
R2. Employees can read their own full row in `employees`, including their salary.
R3. HR employees can read every employee's full row and can update any employee row.
R4. Employees outside HR cannot see anyone else's salary in any way.
R5. Employees outside HR cannot change any employee row, including their own.
R6. Anonymous visitors cannot see the directory or any employee data.
R7. Server-side code using the service role keeps full access, including to the directory.

RLSBENCH-CANARY-f9002c750838f00b
