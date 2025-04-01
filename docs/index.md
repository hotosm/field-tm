# 🤗 Welcome To The Field Mapping Documentation 🤗

## What is ONE thing all the greatest solutions out there have in common?

They never forget the people they are building for (^^) :smiley:

So who are we building field mapping solutions for? In short, we build solutions
for:

### The field mapping manager (coordinating field mapping)

The field mapping manager is responsible for coordinating field
mapping activities, ensuring the accuracy and completeness of the data
collected, and managing the data itself. This involves a number of key
steps, including:

- **_Planning:_** The field mapping manager must develop a clear plan
  for the data collection process, including identifying key areas of
  focus and establishing timelines and targets.

- **_Recruitment:_** The field mapping manager must recruit and train
  field mappers, ensuring that they have the necessary skills and
  expertise to collect accurate and high-quality data.

- **_Coordination:_** The field mapping manager must coordinate the activities
  of the field mappers, ensuring that they are working together
  effectively and efficiently.

  <img
      align="left"
      width="500px"
      src="https://user-images.githubusercontent.com/107098623/194864145-598d6212-9e0b-4c9d-ba90-92e5cd3fa488.png"
      alt="coordination"
    />

### The field mapper (collecting data)

The field mapper is responsible for collecting data in the field. To
ensure the success of the field mapper, we must consider a number of key
factors. These include:

- **_Ease of use:_** The field mapper must be able to easily and efficiently
  collect data, without requiring extensive training or technical
  expertise.

- **_Accessibility:_** The field mapper must be able to access and
  collect data from a wide range of environments, including remote or
  hard-to-reach locations.

- **_Data quality:_** The field mapper must be able to ensure the accuracy and
  completeness of the data they collect, as well as identify and address
  any errors or issues that arise.

### The validator (quality checking the data)

The validator is responsible for quality checking the data collected by
the field mapper, ensuring that it is accurate, complete, and free from
errors. The validator faces a number of challenges and issues, including:

- **_Incomplete or inaccurate data:_** The validator must identify and
  address any data that is incomplete, inaccurate, or otherwise flawed.

- **_Conflicting data:_** The validator may encounter data that
  conflicts with other data sources, requiring them to identify and
  resolve any discrepancies.

- **_Data validation protocols:_** The validator must adhere to strict
  validation protocols and guidelines, ensuring that the data meets a high
  level of quality and accuracy.

## Detailed role breakdown

[Click here][1] to see an overview of who you are building for, which actions
they take and some ideas for solutions!

Below is an overview of the user flow of the **Field Mapper**, the
**Mapping Coordinator / Field Mapping Manager** and the **Validator**.

### The Field Mapping Manager (The person who coordinates field mapping)

The **Field Mapping Manager** is tasked with coordinating all mapping
activities, ensuring that **Field Mappers** are safe and qualified to
work, as well as monitoring data quality. The **Field Mapping
Manager** has to consider 3 main activities:

1. **Pre-field data collection activities**
   - Setting up and testing tools
   - Creating a form
   - Training field mappers (making sure that they understand the form and how
     to fill it)
   - Creating an area of interest within the location to be mapped
2. **Data collection activities**
   - Preparing daily, weekly and monthly activity plans
   - Deploying team (assessing safety and qualifications of mappers)
   - Data quality monitoring
3. **Post-field data collection activities**
   - Daily review of data
   - Giving and receiving team feedback
   - Updating tools and methodoligies

If you want more information, click on [this][2] virtual whiteboard! to see all
the steps a **Field Mapping Coordinator or Manager** goes through.
Here's a sneak-peek:

- See also data collection approach in [in this training guide<<][3]

![Field mapping coordinator][4]

### The Field Mapper (The person who collects data)

The **Field Mapper** surveys locations and collects data from them. The basic
work flow that a **Field Mapper** has to consider is as follows:

1. Find a phone that:
   - Has mobile data or an internet plan.
   - Works well with the app.(ODK Collect)
2. Access the **OSM** registration site and register.
   - https://www.openstreetmap.org/
3. Install ODK Collect on your phone, by clicking the link bellow
  and following the procedure.
   - https://fmtm.hotosm.org/ 
   - Click in the humberg icon on the top right side of your screen.
   - Click Download Custom ODK Collect. 
4. From the FMTM page, choose a campaign.
5. Select a task from the campaign.
   - Scan the QR code that will be displayed after selecting the task. 
6. Launch the map app which allows you to see the moving map of the points that
   you are now responsible for.
7. Complete each point within the task, making sure to answer the questions in
   the form for each one.
8. Send the data of each point until the task is complete.
9. Once the task is complete, signal that your task is finished. This lets the
   **Validator** know that they can check the quality of your data.

If you want to see this workflow in more detail, click on
[this virtual whiteboard!][5]

Here's a sneak-peek:

<img
  align="centre"
  width="1000px"
  height="600px"
  src="https://user-images.githubusercontent.com/107098623/194867381-53813f19-71b1-4342-866f-10c963b7460b.png"
  alt="fmtm-workflow"
/>

### The Validator (The person who checks the quality of data collected)

![osm data collection][6]

The **Validator** does the following tasks to ensure that quality data is
collected and uploaded to **OSM**:

- Logs into task manager
- Checks how many tasks need validation
- Checks tasks for errors
- Stops mappers that make mistakes and explains how they can fix their errors
- Lowers supervision on good mappers in order to spend more time on those who
  are struggling
- Uploads high quality data to **OSM** and marks completed tasks as **done**

Some of the pain points and struggles faced by the **Validator** include:

- Lack of validators (the **Validator** is often the same person as the
  **Field Mapping Manager**)
- Many areas of the world are still unmapped on online commercial maps
- The quality of maps needs to improve
- The more developers complicate tools, the more they reduce the usefulness
  of the tools

For more details, click on [this virtual whiteboard!][7]

See sneak-peek below.

- See also all steps of validation [>>in this training guide<<][8]
- See also global validator Becky's OSM diary which features:
  ["Common Feedback I give while Validating Building Projects"][9]

![validator flow][10]

Some of the key points covered are:

- Understanding the mapping project and the intended use of the collected data
- Verifying the accuracy and completeness of the collected data
- Ensuring consistency with existing data and standards
- Providing clear and constructive feedback to field mappers and coordinators

Overall, understanding the needs and considerations of each of these three user
groups is essential for building effective field mapping solutions.

[1]: https://miro.com/app/board/uXjVPX4XLcI=/?moveToWidget=3458764534814634286&cot=14
[2]: https://miro.com/app/board/uXjVPX4XLcI=/?moveToWidget=3458764535077658755&cot=14
[3]: https://hotosm.github.io/pdc-documentation/en/pages/01-osm-field-surveyor-guideliness/01-metodologi-pengumpulan-data/01_metodologi_pengumpulan_data/
[4]: https://user-images.githubusercontent.com/107098623/194859584-31dae52a-e918-4cd8-9071-24791750d6bb.png
[5]: https://miro.com/app/board/uXjVPX4XLcI=/?moveToWidget=3458764535074723879&cot=14
[6]: https://user-images.githubusercontent.com/107098623/196922048-c156b8ed-7f1a-404b-a636-fcfca2c0b328.png
[7]: https://miro.com/app/board/uXjVPX4XLcI=/?moveToWidget=3458764535077160536&cot=14
[8]: https://hotosm.github.io/pdc-documentation/en/pages/04-data-validation-and-quality-assurance/02-penggunaan-josm-untuk-validasi-data-survei/josm-for-validating-survey-data
[9]: https://www.openstreetmap.org/user/Becky%20Candy/diary/399055
[10]: https://user-images.githubusercontent.com/107098623/194870234-fa9497cb-d9e4-43ff-b7dd-ad731f8be488.png
