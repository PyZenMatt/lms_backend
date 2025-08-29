import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar"
import { Textarea } from "./ui/textarea"
import { 
  ArrowLeft, 
  Play, 
  CheckCircle, 
  Lock, 
  Clock, 
  FileText, 
  Upload,
  BookOpen,
  Target,
  Award,
  Users,
  Star
} from "lucide-react"
import { useAuth } from "./AuthContext"
import { ImageWithFallback } from "./figma/ImageWithFallback"
import { toast } from "sonner"

interface Lesson {
  id: string
  title: string
  description: string
  duration: string
  videoUrl?: string
  content: string
  exercise?: {
    title: string
    description: string
    instructions: string
    timeEstimate: string
    completed?: boolean
    submission?: string
  }
  completed: boolean
  locked: boolean
  order: number
}

interface Course {
  id: string
  title: string
  description: string
  instructor: string
  instructorAvatar: string
  thumbnail: string
  level: 'beginner' | 'intermediate' | 'advanced'
  duration: string
  students: number
  rating: number
  reviews: number
  progress: number
  lessons: Lesson[]
}

interface CourseViewerProps {
  courseId: string
  onBack: () => void
  onNavigateToPage?: (page: string) => void
}

export function CourseViewer({ courseId, onBack, onNavigateToPage }: CourseViewerProps) {
  const { user, updateTokens } = useAuth()
  const [selectedLesson, setSelectedLesson] = useState<string | null>(null)
  const [exerciseSubmission, setExerciseSubmission] = useState("")

  // Mock course data - in real app, this would come from API
  const course: Course = {
    id: courseId,
    title: 'Digital Painting Fundamentals',
    description: 'Master the basics of digital art creation with professional techniques and industry-standard workflows.',
    instructor: 'Prof. Sarah Mitchell',
    instructorAvatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face',
    thumbnail: 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=600&h=300&fit=crop',
    level: 'beginner',
    duration: '8 weeks',
    students: 1247,
    rating: 4.8,
    reviews: 156,
    progress: 65,
    lessons: [
      {
        id: '1',
        title: 'Introduction to Digital Art',
        description: 'Overview of digital art tools and basic concepts',
        duration: '15 min',
        content: 'Welcome to Digital Painting Fundamentals! In this lesson, we\'ll explore the essential tools and concepts that form the foundation of digital art creation...',
        completed: true,
        locked: false,
        order: 1
      },
      {
        id: '2',
        title: 'Setting Up Your Workspace',
        description: 'Configuring your digital art software and hardware',
        duration: '20 min',
        content: 'A well-organized workspace is crucial for productive digital art creation. Let\'s walk through setting up your canvas, brushes, and workspace layout...',
        exercise: {
          title: 'Workspace Setup',
          description: 'Create and customize your first digital workspace',
          instructions: '1. Open your digital art software\n2. Create a new canvas (1920x1080px)\n3. Set up a basic brush palette\n4. Organize your tool panels\n5. Save your workspace preset',
          timeEstimate: '30 minutes',
          completed: true,
          submission: 'I set up my workspace with custom brush presets and organized panels. The 1920x1080 canvas works great for my screen resolution!'
        },
        completed: true,
        locked: false,
        order: 2
      },
      {
        id: '3',
        title: 'Understanding Light and Shadow',
        description: 'Fundamental principles of lighting in digital art',
        duration: '25 min',
        content: 'Light and shadow are the building blocks of realistic digital art. Understanding how light behaves will transform your artwork from flat to dimensional...',
        exercise: {
          title: 'Light Study Practice',
          description: 'Create a simple sphere with realistic lighting',
          instructions: '1. Draw a perfect circle\n2. Establish your light source direction\n3. Add cast shadow and form shadow\n4. Include reflected light\n5. Add highlights for dimension',
          timeEstimate: '45 minutes',
          completed: false
        },
        completed: false,
        locked: false,
        order: 3
      },
      {
        id: '4',
        title: 'Color Theory Basics',
        description: 'Essential color relationships and harmony',
        duration: '30 min',
        content: 'Color theory provides the framework for creating harmonious and impactful artwork. We\'ll explore color wheels, temperature, and emotional impact...',
        exercise: {
          title: 'Color Palette Creation',
          description: 'Design complementary color palettes',
          instructions: '1. Choose a base color\n2. Find its complement\n3. Create triadic variations\n4. Test warm vs cool temperatures\n5. Apply to a simple composition',
          timeEstimate: '40 minutes'
        },
        completed: false,
        locked: true,
        order: 4
      },
      {
        id: '5',
        title: 'Brush Techniques',
        description: 'Mastering different brush strokes and textures',
        duration: '35 min',
        content: 'Different brush techniques create various textures and effects. Master these fundamental strokes to expand your artistic vocabulary...',
        completed: false,
        locked: true,
        order: 5
      }
    ]
  }

  const currentLesson = selectedLesson ? course.lessons.find(l => l.id === selectedLesson) : null
  const completedLessons = course.lessons.filter(l => l.completed).length
  const totalLessons = course.lessons.length

  const handleCompleteLesson = (lessonId: string) => {
    // Mark lesson as complete and unlock next lesson
    updateTokens(5) // Reward for completing lesson
    toast("Lesson completed! ✨", {
      description: "You earned 5 tokens. Next lesson unlocked!"
    })
  }

  const handleSubmitExercise = (lessonId: string) => {
    if (!exerciseSubmission.trim()) {
      toast("Please add your submission before submitting")
      return
    }
    
    updateTokens(10) // Reward for exercise submission
    setExerciseSubmission("")
    toast("Exercise submitted! ✨", {
      description: "You earned 10 tokens. Your work will be sent for peer review.",
      action: {
        label: "Review Others",
        onClick: () => onNavigateToPage?.('peer-review')
      }
    })
  }

  const LessonSidebar = () => (
    <div className="w-80 border-r bg-muted/20 p-4 space-y-4 overflow-y-auto">
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <ImageWithFallback
            src={course.instructorAvatar}
            alt={course.instructor}
            className="size-10 rounded-full"
          />
          <div>
            <h4 className="font-medium">{course.instructor}</h4>
            <p className="font-size: var(--text-sm) text-muted-foreground">Course Instructor</p>
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between font-size: var(--text-sm)">
            <span>Course Progress</span>
            <span>{Math.round((completedLessons / totalLessons) * 100)}%</span>
          </div>
          <Progress value={(completedLessons / totalLessons) * 100} className="h-2" />
          <p className="font-size: var(--text-xs) text-muted-foreground">
            {completedLessons} of {totalLessons} lessons completed
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <h4 className="font-medium">Course Content</h4>
        <div className="space-y-1">
          {course.lessons.map((lesson) => (
            <button
              key={lesson.id}
              onClick={() => !lesson.locked && setSelectedLesson(lesson.id)}
              disabled={lesson.locked}
              className={`w-full p-3 rounded-lg text-left transition-colors ${
                selectedLesson === lesson.id 
                  ? 'bg-primary text-primary-foreground' 
                  : lesson.locked 
                    ? 'bg-muted/50 text-muted-foreground cursor-not-allowed'
                    : 'hover:bg-muted'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  {lesson.completed ? (
                    <CheckCircle className="size-5 text-green-600" />
                  ) : lesson.locked ? (
                    <Lock className="size-5" />
                  ) : (
                    <Play className="size-5" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <h5 className="font-medium font-size: var(--text-sm) truncate">
                    {lesson.order}. {lesson.title}
                  </h5>
                  <div className="flex items-center gap-2 font-size: var(--text-xs) opacity-80">
                    <Clock className="size-3" />
                    <span>{lesson.duration}</span>
                    {lesson.exercise && (
                      <>
                        <Target className="size-3" />
                        <span>Exercise</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )

  const LessonContent = () => {
    if (!currentLesson) {
      return (
        <div className="flex-1 flex items-center justify-center text-center p-8">
          <div>
            <BookOpen className="size-16 mx-auto mb-4 text-muted-foreground" />
            <h3 className="font-size: var(--text-lg) font-medium mb-2">Select a Lesson</h3>
            <p className="text-muted-foreground">
              Choose a lesson from the sidebar to start learning
            </p>
          </div>
        </div>
      )
    }

    return (
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2>{currentLesson.title}</h2>
              <p className="text-muted-foreground">{currentLesson.description}</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1 font-size: var(--text-sm) text-muted-foreground">
                <Clock className="size-4" />
                <span>{currentLesson.duration}</span>
              </div>
              {!currentLesson.completed && !currentLesson.locked && (
                <Button onClick={() => handleCompleteLesson(currentLesson.id)}>
                  <CheckCircle className="size-4 mr-2" />
                  Mark Complete
                </Button>
              )}
            </div>
          </div>

          {currentLesson.completed && (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="size-5 text-green-600" />
              <span className="font-size: var(--text-sm) font-medium text-green-800">
                Lesson Completed ✨
              </span>
            </div>
          )}
        </div>

        <Tabs defaultValue="content" className="space-y-4">
          <TabsList>
            <TabsTrigger value="content">Lesson Content</TabsTrigger>
            {currentLesson.exercise && (
              <TabsTrigger value="exercise">Exercise</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="content" className="space-y-4">
            <Card>
              <CardContent className="p-6">
                <div className="prose max-w-none">
                  <p>{currentLesson.content}</p>
                  
                  {/* Mock video player */}
                  <div className="mt-6 bg-black rounded-lg aspect-video flex items-center justify-center">
                    <div className="text-center text-white">
                      <Play className="size-16 mx-auto mb-4 opacity-80" />
                      <p className="font-size: var(--text-lg) font-medium">Video Lesson</p>
                      <p className="font-size: var(--text-sm) opacity-80">Click to play lesson video</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {currentLesson.exercise && (
            <TabsContent value="exercise" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="size-5" />
                    {currentLesson.exercise.title}
                  </CardTitle>
                  <CardDescription>{currentLesson.exercise.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium mb-2">Instructions</h4>
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <pre className="whitespace-pre-wrap font-size: var(--text-sm)">{currentLesson.exercise.instructions}</pre>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Time Estimate</h4>
                        <Badge variant="outline">{currentLesson.exercise.timeEstimate}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Reward</h4>
                        <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                          +10 ✨
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {currentLesson.exercise.completed ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <CheckCircle className="size-5 text-green-600" />
                        <span className="font-size: var(--text-sm) font-medium text-green-800">
                          Exercise Completed ✨
                        </span>
                      </div>
                      {currentLesson.exercise.submission && (
                        <div className="space-y-2">
                          <h4 className="font-medium">Your Submission</h4>
                          <div className="p-4 border rounded-lg bg-muted/50">
                            <p className="font-size: var(--text-sm)">{currentLesson.exercise.submission}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <h4 className="font-medium">Submit Your Work</h4>
                        <Textarea
                          placeholder="Describe your exercise completion, attach images, or share your process..."
                          value={exerciseSubmission}
                          onChange={(e) => setExerciseSubmission(e.target.value)}
                          className="min-h-24"
                        />
                      </div>
                      <div className="flex items-center gap-3">
                        <Button onClick={() => handleSubmitExercise(currentLesson.id)}>
                          <Upload className="size-4 mr-2" />
                          Submit Exercise
                        </Button>
                        <Button variant="outline">
                          <FileText className="size-4 mr-2" />
                          Attach Files
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-16 items-center px-6">
          <Button variant="ghost" onClick={onBack} className="mr-4">
            <ArrowLeft className="size-4 mr-2" />
            Back to Courses
          </Button>
          <div className="flex-1">
            <h1 className="font-size: var(--text-lg) font-medium">{course.title}</h1>
            <div className="flex items-center gap-4 font-size: var(--text-sm) text-muted-foreground">
              <div className="flex items-center gap-1">
                <Users className="size-3" />
                <span>{course.students} students</span>
              </div>
              <div className="flex items-center gap-1">
                <Star className="size-3" />
                <span>{course.rating} ({course.reviews} reviews)</span>
              </div>
              <Badge variant="outline" className="capitalize">
                {course.level}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <LessonSidebar />
        <LessonContent />
      </div>
    </div>
  )
}