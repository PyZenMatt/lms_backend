import { useState, useEffect } from "react"
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
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { markLessonComplete } from '@/services/lessons'
import { useCourseOutline } from '@/hooks/useCourseOutline'
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
  const { updateTokens } = useAuth()
  const [selectedLesson, setSelectedLesson] = useState<string | null>(null)
  const [exerciseSubmission, setExerciseSubmission] = useState("")

  // Fetch real data via hook
  const { data, isLoading, isError, error } = useCourseOutline(courseId)

  // Map API lessons into local shape
  const apiLessons = data?.lessons ?? []
  const course: Course = {
    id: String(courseId),
    title: data?.course?.title ?? "Caricamento...",
    description: "",
    instructor: data?.course?.teacher?.username ?? "",
    instructorAvatar: data?.course?.cover ?? "",
    thumbnail: data?.course?.cover ?? "",
    level: 'beginner',
    duration: '',
    students: 0,
    rating: 0,
    reviews: 0,
    progress: data?.progress?.percent ?? 0,
    lessons: apiLessons.map((l, idx) => ({
      id: String(l.id ?? idx),
      title: l.title ?? `Lezione ${idx + 1}`,
      description: "",
      duration: l.duration_sec ? `${Math.round((l.duration_sec || 0) / 60)} min` : "",
      content: "",
      completed: !!data?.progress?.completed_lesson_ids?.includes(l.id),
      locked: data?.course?.enrollment_status !== 'enrolled' && !l.is_free_preview,
      order: l.position ?? idx + 1,
    }))
  }

  useEffect(() => {
    if (isError) {
      toast(String((error as unknown as Error)?.message ?? String(error)))
    }
  }, [isError, error])

  const currentLesson = selectedLesson ? course.lessons.find(l => l.id === selectedLesson) : null
  const completedLessons = course.lessons.filter(l => l.completed).length
  const totalLessons = course.lessons.length

  const handleCompleteLesson = (lessonId: string) => {
    // use mutation instead of local mock
  void markCompleteMutation.mutateAsync(Number(lessonId))
  }

  const qc = useQueryClient()
  const markCompleteMutation = useMutation({
    mutationFn: async (lessonId: number) => {
      const res = await markLessonComplete(lessonId)
      if (!res.ok) throw res.error || new Error('Failed to mark complete')
      return res.data
    },
  onSuccess: () => {
      // reward tokens locally and invalidate outline
      updateTokens(5)
      toast("Lesson completed! ✨", {
        description: "You earned 5 tokens. Next lesson unlocked!"
      })
      try {
        qc.invalidateQueries({ queryKey: ['courseOutline', Number(courseId ?? '')] })
      } catch {
        // fallback: refetch local hook if available
      }
    },
    onError: (err: unknown) => {
      const msg = err && typeof err === 'object' && 'message' in err ? (err as any).message : String(err)
      toast(String(msg))
    }
  })

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
            <p className="text-sm text-muted-foreground">Course Instructor</p>
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Course Progress</span>
            <span>{Math.round((completedLessons / totalLessons) * 100)}%</span>
          </div>
          <Progress value={(completedLessons / totalLessons) * 100} className="h-2" />
          <p className="text-xs text-muted-foreground">
            {completedLessons} of {totalLessons} lessons completed
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <h4 className="font-medium">Course Content</h4>
        <div className="space-y-1">
          {isLoading ? (
            <div className="p-4">Caricamento lezioni…</div>
          ) : (
            course.lessons.map((lesson) => (
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
                    <h5 className="font-medium text-sm truncate">
                      {lesson.order}. {lesson.title}
                    </h5>
                    <div className="flex items-center gap-2 text-xs opacity-80">
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
            ))
          )}
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
            <h3 className="text-lg font-medium mb-2">Select a Lesson</h3>
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
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
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
              <span className="text-sm font-medium text-green-800">
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
                      <p className="text-lg font-medium">Video Lesson</p>
                      <p className="text-sm opacity-80">Click to play lesson video</p>
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
                        <pre className="whitespace-pre-wrap text-sm">{currentLesson.exercise.instructions}</pre>
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
                        <span className="text-sm font-medium text-green-800">
                          Exercise Completed ✨
                        </span>
                      </div>
                      {currentLesson.exercise.submission && (
                        <div className="space-y-2">
                          <h4 className="font-medium">Your Submission</h4>
                          <div className="p-4 border rounded-lg bg-muted/50">
                            <p className="text-sm">{currentLesson.exercise.submission}</p>
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
            <h1 className="text-lg font-medium">{course.title}</h1>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
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
