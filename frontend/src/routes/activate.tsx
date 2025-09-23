import {
    createFileRoute,
    redirect,
} from "@tanstack/react-router"

import useAuth, { isLoggedIn } from "../hooks/useAuth"
import {useEffect} from "react";

export const Route = createFileRoute("/activate")({
    component: Activate,
    beforeLoad: async () => {
        if (isLoggedIn()) {
            throw redirect({
                to: "/",
            })
        }
    },
})

function Activate() {
    const { activateMutation } = useAuth()

    useEffect(() => {
        activateMutation.mutate()
    }, []);

    return <></>
}

export default Activate
