"""Pre-populated demo data for STEMBOOST.

Call seed(data_service) to populate the database with sample users,
learning paths, courses, content, assignments, and opportunities.
"""


def seed(ds):
    """Populate the database with demo data.

    Args:
        ds: A connected DataService instance.
    """
    # ---- Educators ----
    edu1_id = ds.create_user(
        username="dr.smith", email="smith@university.edu",
        password="pass123", name="Dr. Smith", role="educator",
        expertise_areas=["Computer Science", "Data Science"])
    edu2_id = ds.create_user(
        username="prof.chen", email="chen@university.edu",
        password="pass123", name="Prof. Chen", role="educator",
        expertise_areas=["Mathematics", "Physics"])

    # ---- Mentors ----
    men1_id = ds.create_user(
        username="ms.jones", email="jones@stemboost.org",
        password="pass123", name="Ms. Jones", role="mentor")
    men2_id = ds.create_user(
        username="mr.williams", email="williams@stemboost.org",
        password="pass123", name="Mr. Williams", role="mentor")

    # ---- Learners ----
    lea1_id = ds.create_user(
        username="alex", email="alex@mail.com",
        password="pass123", name="Alex", role="learner",
        vision_type="blind",
        accessibility_prefs={"audio": True, "high_contrast": True,
                             "large_text": False},
        stem_interests=["Computer Science", "Data Science"],
        mentor_id=men1_id)
    lea2_id = ds.create_user(
        username="sam", email="sam@mail.com",
        password="pass123", name="Sam", role="learner",
        vision_type="low_vision",
        accessibility_prefs={"audio": True, "high_contrast": False,
                             "large_text": True},
        stem_interests=["Mathematics", "Engineering"],
        mentor_id=men1_id)
    lea3_id = ds.create_user(
        username="jordan", email="jordan@mail.com",
        password="pass123", name="Jordan", role="learner",
        vision_type="blind",
        accessibility_prefs={"audio": True, "high_contrast": True,
                             "large_text": True},
        stem_interests=["Biology", "Chemistry"],
        mentor_id=men2_id)

    # ---- Learning Path 1: Intro to Programming (Job Exploration) ----
    path1_id = ds.create_learning_path(
        title="Introduction to Programming",
        description="A beginner-friendly path covering programming fundamentals "
                    "and career opportunities in software development.",
        category="Job Exploration",
        created_by=edu1_id)

    c1_id = ds.create_course(
        title="What is Programming?",
        description="An overview of programming and why it matters in STEM.",
        path_id=path1_id, created_by=edu1_id, order_index=1)
    ds.create_content(
        title="Welcome to Programming",
        text_body=(
            "Programming is the process of writing instructions that a computer "
            "can execute. These instructions, called code, tell the computer what "
            "to do step by step. Programming is used in almost every STEM field "
            "today, from analyzing scientific data to controlling robotic systems. "
            "In this course you will learn what programming is, why it is "
            "important, and what career paths are available to programmers."
        ),
        course_id=c1_id, created_by=edu1_id, order_index=1)

    c2_id = ds.create_course(
        title="Variables and Data Types",
        description="Learn how computers store and organize information.",
        path_id=path1_id, created_by=edu1_id, order_index=2)
    ds.create_content(
        title="Understanding Variables",
        text_body=(
            "A variable is a named container that holds a value in a computer "
            "program. Think of it like a labeled box where you can store "
            "information. Variables can hold different types of data: numbers, "
            "text, or true and false values. For example, you might create a "
            "variable called age and store the number 25 in it. Understanding "
            "variables is the first step to writing useful programs."
        ),
        course_id=c2_id, created_by=edu1_id, order_index=1)

    c3_id = ds.create_course(
        title="Careers in Software Development",
        description="Explore career paths available to programmers.",
        path_id=path1_id, created_by=edu1_id, order_index=3)
    ds.create_content(
        title="Software Career Paths",
        text_body=(
            "Software development offers many career paths. Web developers "
            "build websites and online applications. Data scientists analyze "
            "large datasets to find patterns. Mobile developers create "
            "applications for phones and tablets. DevOps engineers manage the "
            "systems that run software in production. Accessibility engineers "
            "ensure that software is usable by people of all abilities. Each "
            "of these roles requires programming skills and offers strong "
            "job growth and competitive salaries."
        ),
        course_id=c3_id, created_by=edu1_id, order_index=1)

    # ---- Learning Path 2: Math Foundations (Post-Secondary Ed) ----
    path2_id = ds.create_learning_path(
        title="Mathematics Foundations for STEM",
        description="Build a solid math foundation for further study in any "
                    "STEM discipline.",
        category="Post-Secondary Education",
        created_by=edu2_id)

    c4_id = ds.create_course(
        title="Algebra Basics",
        description="Review fundamental algebra concepts.",
        path_id=path2_id, created_by=edu2_id, order_index=1)
    ds.create_content(
        title="Introduction to Algebra",
        text_body=(
            "Algebra is the branch of mathematics that uses letters and symbols "
            "to represent numbers and quantities in equations. For example, in "
            "the equation x plus 3 equals 7, the letter x represents an unknown "
            "value that we can solve for. Algebra is essential for every STEM "
            "field because it provides the tools to describe relationships "
            "between quantities and solve problems systematically."
        ),
        course_id=c4_id, created_by=edu2_id, order_index=1)

    c5_id = ds.create_course(
        title="Statistics and Probability",
        description="Learn how to analyze data and understand chance.",
        path_id=path2_id, created_by=edu2_id, order_index=2)
    ds.create_content(
        title="What is Statistics?",
        text_body=(
            "Statistics is the science of collecting, organizing, and "
            "interpreting data. It helps us make decisions based on evidence "
            "rather than guesses. For example, a scientist might use statistics "
            "to determine whether a new medicine is effective. Probability is "
            "closely related and deals with how likely events are to occur. "
            "Together, statistics and probability are used in fields from "
            "medicine to engineering to finance."
        ),
        course_id=c5_id, created_by=edu2_id, order_index=1)

    # ---- Learning Path 3: Workplace Readiness ----
    path3_id = ds.create_learning_path(
        title="STEM Workplace Readiness",
        description="Develop professional skills needed to succeed in STEM "
                    "work environments.",
        category="Workplace Readiness",
        created_by=edu1_id)

    c6_id = ds.create_course(
        title="Communication in STEM Teams",
        description="Learn to communicate effectively in technical teams.",
        path_id=path3_id, created_by=edu1_id, order_index=1)
    ds.create_content(
        title="Technical Communication",
        text_body=(
            "Effective communication is one of the most important skills in "
            "any STEM workplace. You will need to explain complex ideas to "
            "teammates, write clear documentation, and present your work to "
            "non-technical stakeholders. Good communicators listen actively, "
            "ask clarifying questions, and adapt their language to their "
            "audience. In this unit you will learn strategies for clear "
            "written and verbal communication in technical settings."
        ),
        course_id=c6_id, created_by=edu1_id, order_index=1)

    c7_id = ds.create_course(
        title="Assistive Technology in the Workplace",
        description="Understand tools that support accessible work environments.",
        path_id=path3_id, created_by=edu1_id, order_index=2)
    ds.create_content(
        title="Assistive Tech Overview",
        text_body=(
            "Assistive technology includes tools and software that help people "
            "with disabilities perform tasks that might otherwise be difficult "
            "or impossible. Screen readers convert text to speech so blind "
            "users can interact with computers. Screen magnifiers enlarge "
            "content for users with low vision. Braille displays translate "
            "on-screen text into braille. Voice recognition software allows "
            "hands-free computer control. Knowing how to use and advocate for "
            "assistive technology is valuable in any STEM workplace."
        ),
        course_id=c7_id, created_by=edu1_id, order_index=1)

    # ---- Assignments ----
    # Ms. Jones assigns Path 1 to Alex (exclude course 3)
    ds.create_assignment(
        mentor_id=men1_id, learner_id=lea1_id, path_id=path1_id,
        excluded_course_ids=[c3_id], assigned_date="2026-03-15")

    # Ms. Jones assigns Path 2 to Sam (no exclusions)
    ds.create_assignment(
        mentor_id=men1_id, learner_id=lea2_id, path_id=path2_id,
        excluded_course_ids=[], assigned_date="2026-03-16")

    # Mr. Williams assigns Path 3 to Jordan
    ds.create_assignment(
        mentor_id=men2_id, learner_id=lea3_id, path_id=path3_id,
        excluded_course_ids=[], assigned_date="2026-03-17")

    # ---- Opportunities ----
    ds.create_opportunity(
        title="Summer Data Science Internship",
        description="A 10-week paid internship at TechCorp focused on "
                    "data analysis and machine learning. Open to learners "
                    "with an interest in data science. Accessible workplace "
                    "with full assistive technology support.",
        opp_type="internship",
        posted_by=men1_id,
        posted_date="2026-03-10")

    ds.create_opportunity(
        title="STEM Bridge Scholarship Program",
        description="Full scholarship for a one-year certificate program "
                    "in applied mathematics or computer science at State "
                    "University. Priority given to learners with disabilities.",
        opp_type="academic",
        posted_by=men2_id,
        posted_date="2026-03-12")
