import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"

import { AxiosError } from "axios"
import {
  type Body_login_login_access_token as AccessToken,
  type ApiError,
  LoginService,
  type UserPublic,
  type UserRegister,
  UsersService,
  OpenAPI,
} from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"
import {getUrl} from "../client/core/request.ts";

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

const useAuth = () => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const {showSuccessToast, showErrorToast} = useCustomToast()
  const queryClient = useQueryClient()
  const { data: user, isLoading } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
    enabled: isLoggedIn(),
  })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),

    onSuccess: () => {
      navigate({ to: "/login" })
      showSuccessToast(
        "Account created. Check your e-mails to activate your account.",
      )
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      showErrorToast(errDetail)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      formData: data,
    })
    localStorage.setItem("access_token", response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const loginSSOFusionAuth = async (app: string) => {
    const loginPopup = window.open(
        getUrl(OpenAPI, {
          method: "GET",
          url: `/api/v1/auth/sso/fusionauth/${app}/login-html`,
          mediaType: "application/x-www-form-urlencoded",
          errors: {
            422: "Validation Error",
          },
        }),
        'Login',
        'width=600,height=700'
    )
    window.addEventListener('message', (event) => {
      if (event.data?.access_token) {
        localStorage.setItem("access_token", event.data.access_token)
        loginPopup?.close()
        navigate({ to: "/" })
      }
    })
  }

  const loginSSOFusionAuthMutation = useMutation({
    mutationFn: loginSSOFusionAuth,
    onSuccess: () => {},
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong"
      }

      showErrorToast(errDetail)
    },
  })

  const activate = async () => {
    const token = new URLSearchParams(window.location.search).get("token")
    if (!token) return
    await UsersService.activateUser({ requestBody: {token: token} })
  }

  const activateMutation = useMutation({
    mutationFn: activate,
    onSuccess: () => {
      navigate({ to: "/login" })
      showSuccessToast(
          "Your account has been activated successfully.",
      )
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      navigate({ to: "/login" })
      showErrorToast(errDetail)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const logout = () => {
    localStorage.removeItem("access_token")
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    activateMutation,
    loginMutation,
    loginSSOFusionAuthMutation,
    logout,
    user,
    isLoading,
    error,
    resetError: () => setError(null),
  }
}

export { isLoggedIn }
export default useAuth
