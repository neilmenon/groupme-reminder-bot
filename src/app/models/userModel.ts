export class UserModel {
    id: number
    name: string
    num_reminders: number
    image_url: string
    access_token: string
    bot_groups: Array<any>

    constructor() {

    }
}

export class ReminderModel {
    id: number
    text: string
    timestamp: string
    frequency: number
    group_id: number
}