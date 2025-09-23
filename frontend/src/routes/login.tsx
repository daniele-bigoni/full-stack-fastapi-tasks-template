import {
    Container,
    Image,
    Input,
    Text,
    Flex,
    Center,
    Box,
    Separator,
    HStack
} from "@chakra-ui/react"
import {
  createFileRoute,
  Link as RouterLink,
  redirect,
} from "@tanstack/react-router"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiLock, FiMail } from "react-icons/fi"

import type { Body_login_login_access_token as AccessToken } from "@/client"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import { InputGroup } from "@/components/ui/input-group"
import { PasswordInput } from "@/components/ui/password-input"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"
import Logo from "/assets/images/fastapi-logo.svg"
import { emailPattern, passwordRules } from "../utils"

export const Route = createFileRoute("/login")({
  component: Login,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({
        to: "/",
      })
    }
  },
})

function Login() {
  const {
    loginMutation,
    error,
    resetError,
    loginSSOFusionAuthMutation,
  } = useAuth()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<AccessToken>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      username: "",
      password: "",
    },
  })

  const onSubmitLogin: SubmitHandler<AccessToken> = async (data) => {
    if (isSubmitting) return

    resetError()

    try {
      await loginMutation.mutateAsync(data)
    } catch {
      // error is handled by useAuth hook
    }
  }

  const onClickSSOFusionAuthAppA = async () => {
    resetError()

    try {
      await loginSSOFusionAuthMutation.mutateAsync("app-a")
    } catch {
      // error is handled by useAuth hook
    }
  }

  const onClickSSOFusionAuthAppB = async () => {
    resetError()

    try {
      await loginSSOFusionAuthMutation.mutateAsync("app-b")
    } catch {
      // error is handled by useAuth hook
    }
  }

  return (
    <Center>
      <Flex
          direction="column"
          maxW="md"
          alignItems="stretch"
          justifyContent="center"
          gap={4}
          h="100vh"
      >
        <Container
          as="form"
          onSubmit={handleSubmit(onSubmitLogin)}
          //h="50vh"
          maxW="sm"
          alignItems="stretch"
          justifyContent="center"
          gap={4}
          centerContent
        >
          <Image
            src={Logo}
            alt="FastAPI logo"
            height="auto"
            maxW="2xs"
            alignSelf="center"
            mb={4}
          />
          <Field
            invalid={!!errors.username}
            errorText={errors.username?.message || !!error}
          >
            <InputGroup w="100%" startElement={<FiMail />}>
              <Input
                {...register("username", {
                  required: "Username is required",
                  pattern: emailPattern,
                })}
                placeholder="Email"
                type="email"
              />
            </InputGroup>
          </Field>
          <PasswordInput
            type="password"
            startElement={<FiLock />}
            {...register("password", passwordRules())}
            placeholder="Password"
            errors={errors}
          />
          <RouterLink to="/recover-password" className="main-link">
            Forgot Password?
          </RouterLink>
          <Button variant="solid" type="submit" loading={isSubmitting} size="md">
            Log In
          </Button>
          <Text>
            Don't have an account?{" "}
            <RouterLink to="/signup" className="main-link">
              Sign Up
            </RouterLink>
          </Text>
        </Container>
        <Box position='relative' padding='5'>
          <HStack>
          <Separator flex="1" />
          <Text flexShrink="0">
            OR
          </Text>
          <Separator flex="1" />
          </HStack>
        </Box>
        <Button onClick={onClickSSOFusionAuthAppA}>
          Continue with FusionAuth App A
        </Button>
        <Button onClick={onClickSSOFusionAuthAppB}>
          Continue with FusionAuth App B
        </Button>
      </Flex>
    </Center>
  )
}
