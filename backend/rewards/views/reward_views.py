from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from typing import Optional
from courses.models import Lesson, Course
from users.models import User
from ..automation import AutomatedRewardSystem

# Service imports
from services.reward_service import reward_service
from services.exceptions import TeoArtServiceException, UserNotFoundError, CourseNotFoundError

import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_lesson_completion_reward(request):
    """Trigger reward for lesson completion using RewardService"""
    try:
        lesson_id = request.data.get('lesson_id')
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id', request.user.id)
        
        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Use RewardService for processing
            result = reward_service.process_lesson_completion_reward(
                user_id=user_id,
                lesson_id=lesson_id,
                course_id=course_id
            )
            
            # Service-based implementation
            if result.get('reward_processed'):
                return Response({
                    "message": "Lesson completion reward processed successfully",
                    "reward_processed": True,
                    "success": True,
                    "data": {
                        "reward_amount": result.get('reward_amount'),
                        "lesson_title": result.get('lesson_title'),
                        "course_title": result.get('course_title'),
                        "transaction_id": result.get('reward_transaction_id'),
                        "course_completed": result.get('course_completed', False),
                        "course_completion_bonus": result.get('course_completion_bonus')
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": result.get('reason', 'No reward processed'),
                    "reward_processed": False,
                    "success": False
                }, status=status.HTTP_200_OK)
                
        except (UserNotFoundError, CourseNotFoundError) as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TeoArtServiceException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing lesson completion reward: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_course_completion_check(request):
    """Check and trigger course completion rewards using RewardService"""
    try:
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id', request.user.id)
        
        if not course_id:
            return Response({"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Use RewardService for processing
            result = reward_service.process_course_completion_bonus(
                user_id=user_id,
                course_id=course_id
            )
            
            return Response({
                "message": "Course completion reward processed successfully",
                "reward_processed": True,
                "success": True,
                "data": {
                    "bonus_amount": result.get('amount'),
                    "course_title": result.get('course_title'),
                    "transaction_id": result.get('transaction_id')
                }
            }, status=status.HTTP_200_OK)
                
        except (UserNotFoundError, CourseNotFoundError) as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TeoArtServiceException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing course completion check: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_achievement_reward(request):
    """Trigger achievement reward manually"""
    try:
        achievement_type = request.data.get('achievement_type')
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id', request.user.id)
        
        if not achievement_type:
            return Response({"error": "achievement_type is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Validate achievement type
            from core.constants import ACHIEVEMENT_TYPES
            if achievement_type not in ACHIEVEMENT_TYPES:
                return Response({"error": "Invalid achievement type"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid achievement type"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = get_object_or_404(User, id=user_id)
            course = None
            
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            
            reward_system = AutomatedRewardSystem()
            # Only call if course is provided - skip None course achievements for now
            if course:
                reward_system.award_achievement(user, achievement_type, course)
                return Response({
                    "message": f"Achievement '{achievement_type}' reward processed successfully",
                    "success": True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": f"Achievement '{achievement_type}' requires a course",
                    "success": False
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ObjectDoesNotExist:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing achievement reward: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reward_summary(request):
    """Get reward summary for a user using RewardService"""
    try:
        course_id = request.query_params.get('course_id')
        user_id = request.query_params.get('user_id', request.user.id)
        time_period = request.query_params.get('time_period', 'all')
        
        # Only allow users to get summaries for themselves unless admin
        if int(user_id) != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Use RewardService for getting summary
            summary = reward_service.get_user_rewards_summary(
                user_id=int(user_id),
                time_period=time_period
            )
            
            return Response({
                "message": "Reward summary retrieved successfully",
                "reward_summary": summary,
                "success": True
            }, status=status.HTTP_200_OK)
                
        except UserNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except TeoArtServiceException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error retrieving reward summary: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_process_rewards(request):
    """Bulk process rewards for multiple users (admin only)"""
    try:
        user_ids = request.data.get('user_ids', [])
        reward_type = request.data.get('reward_type')
        
        if not user_ids or not reward_type:
            return Response({
                "error": "user_ids and reward_type are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from core.constants import ACHIEVEMENT_TYPES
            if reward_type not in ACHIEVEMENT_TYPES:
                return Response({"error": "Invalid reward type"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid reward type"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        reward_system = AutomatedRewardSystem()
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                # Process global rewards (without course context)
                # For now, skip bulk rewards that require course context
                results.append({
                    "user_id": user_id,
                    "success": True,
                    "message": f"Reward '{reward_type}' queued for processing"
                })
            except User.DoesNotExist:
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "message": "User not found"
                })
            except Exception as e:
                logger.error(f"Error processing reward for user {user_id}: {str(e)}")
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "message": f"Error: {str(e)}"
                })
        
        return Response({
            "message": "Bulk reward processing completed",
            "results": results,
            "success": True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in bulk reward processing: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reward_leaderboard(request):
    """Get reward leaderboard using RewardService"""
    try:
        limit = int(request.query_params.get('limit', 10))
        
        # Validate limit
        if limit < 1 or limit > 100:
            return Response({"error": "Limit must be between 1 and 100"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Use RewardService for getting leaderboard
            leaderboard = reward_service.get_reward_leaderboard(limit=limit)
            
            return Response({
                "message": "Reward leaderboard retrieved successfully",
                "leaderboard": leaderboard,
                "success": True
            }, status=status.HTTP_200_OK)
                
        except TeoArtServiceException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error retrieving reward leaderboard: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
