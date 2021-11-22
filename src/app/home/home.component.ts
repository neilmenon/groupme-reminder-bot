import { AfterViewInit, Component, OnInit, QueryList, ViewChild, ViewChildren } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatOptionSelectionChange } from '@angular/material/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSelect, MatSelectChange } from '@angular/material/select';
import { MatSort } from '@angular/material/sort';
import * as moment from 'moment';
import { BackendService } from '../backend.service';
import { config } from '../config';
import { ConfirmPopupComponent } from '../confirm-popup/confirm-popup.component';
import { MessageService } from '../message.service';
import { ReminderModel, UserModel } from '../models/userModel';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {  
  moment: any = moment
  user: UserModel
  groups: Array<any> = []
  groupForm: FormGroup
  groupsLoading: boolean = false
  currGroup: any = null
  showReminderForm: boolean = false
  rForm: FormGroup
  isFrequencyChecked: boolean = false
  today: Date = new Date()
  reminders: Array<ReminderModel> = []
  displayedColumns: Array<string> = ['text', 'timestamp', 'frequency', 'sendingIn', 'actions']
  sortOrder: string = "DESC"

  constructor(
    private backendService: BackendService,
    private messageService: MessageService,
    public dialog: MatDialog,
    private fb: FormBuilder
  ) { }

  ngOnInit(): void {
    this.backendService.getUser().toPromise().then((data: any) => {
      if (data?.id) {
        this.user = data
      }
    }).catch(() => {
      this.messageService.open("There was an error while trying to get the logged in user.")
    })

    // form for selecting group
    this.groupForm = this.fb.group({ group: [null] })

    // form for adding reminders
    this.rForm = this.fb.group({
      text: [null, Validators.required],
      date: [null, Validators.required],
      time: [null, Validators.required],
      frequency: [null, Validators.min(1)],
      freqUnit: [null]
    })

    this.rForm.valueChanges.subscribe(() => {
      console.log(this.rForm.getRawValue())
    })
  }

  signOut() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "Sign Out",
        message: `Are you sure you want to sign out?<br>(Signed in as ${this.user.name}).`,
        primaryButton: "Confirm"
      }
    })

    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        window.location.href = config.api_root + '/logout'
      }
    })
  }

  signIn() {
    window.location.href = config.api_root + "/login"
  }

  selectGroup(event: MatSelectChange) {
    this.backendService.getGroupFromDB(event.value?.id).toPromise().then((data: any) => {
      this.currGroup = event.value
      if (data?.id) {
        this.currGroup['isBotRegistered'] = true
        this.getReminders()
        // setTimeout(() => {
        //   console.log(this.sort)
        //   let sortC: MatSort = this.sort.toArray()[0]
        //   console.log(sortC)
        //   sortC.sortChange.subscribe(() => {
        //     console.log(sortC)
        //   })
        // }, 2000)
      } else {
        this.currGroup['isBotRegistered'] = false
      }
    })
    
  }

  loadGroups() {
    this.groupsLoading = true
    this.backendService.getGroups(this.user.access_token).toPromise().then((data: any) => {
      this.groups = data.response
    }).catch(() => {
      this.messageService.open("There was an issue getting your groups. Please try again.")
    }).finally(() => { this.groupsLoading = false })
  }

  isGroupAdmin(group: any) {
    return group.members.filter((x: any) => x.user_id == this.user.id)[0].roles.includes("admin")
  }

  addBot() {
    this.backendService.registerBot(this.currGroup.id).toPromise().then((data: any) => {
      this.currGroup['isBotRegistered'] = true
      this.messageService.open(`Successfully added Reminder Bot to ${this.currGroup.name}!`)
    })
  }

  deleteBot() {
    const dialogRef = this.dialog.open(ConfirmPopupComponent, {
      data: { 
        title: "Remove Bot",
        message: `Are you sure you want to remove Reminder Bot from ${this.currGroup.name}? You can always re-add the bot.`,
        primaryButton: "Confirm"
      }
    })

    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.backendService.deleteBotFromGroup(this.currGroup.id).toPromise().then(() => {
          this.currGroup['isBotRegistered'] = false
          this.messageService.open(`Successfully removed Reminder Bot from ${this.currGroup.name}.`)
        }).catch(() => {
          this.messageService.open("Unable to delete bot. Please try again.")
        })
      }
    })
    
  }

  toggleFrequency() {
    this.isFrequencyChecked = !this.isFrequencyChecked

    if (this.isFrequencyChecked) {
      this.rForm.controls['frequency'].setValidators(Validators.required)
      this.rForm.controls['frequency'].updateValueAndValidity()
      this.rForm.controls['freqUnit'].setValidators(Validators.required)
      this.rForm.controls['freqUnit'].updateValueAndValidity()
    } else {
      this.rForm.controls['frequency'].setValidators([])
      this.rForm.controls['freqUnit'].setValidators([])
      this.rForm.controls['frequency'].setValue(null)
      this.rForm.controls['freqUnit'].setValue(null)
      this.rForm.controls['frequency'].updateValueAndValidity()
      this.rForm.controls['freqUnit'].updateValueAndValidity()
    }
    this.rForm.updateValueAndValidity()
  }

  createReminder() {
    let finalDate: moment.Moment = moment(this.rForm.controls['date'].value).set({ 
      "hour": parseInt(this.rForm.controls['time'].value.split(":")[0]),
      "minute": parseInt(this.rForm.controls['time'].value.split(":")[1])
    })
    let frequencyInMinutes: number = null
    if (this.isFrequencyChecked) {
      let multiplier: number = this.rForm.controls['freqUnit'].value == "minutes" ? 1 : (this.rForm.controls['freqUnit'].value == "hours" ? 60 : 60*24)
      frequencyInMinutes = parseInt(this.rForm.controls['frequency'].value) * multiplier
    }
    
    this.backendService.createReminder(this.currGroup.id, this.rForm.controls['text'].value, finalDate.unix(), frequencyInMinutes).toPromise().then((data: any) => {
      this.messageService.open("Successfully created reminder.")
      this.reminders = data
      this.showReminderForm = false
      this.isFrequencyChecked = false
    }).catch(() => {
      this.messageService.open("There was an error trying to create this reminder.")
    })

  }

  getReminders(sortBy: string = "timestamp", fromTable: boolean = false) {
    let sortOrder: string = "DESC"
    if (fromTable) {
      this.sortOrder = this.sortOrder == "DESC" ? "ASC" : "DESC"
      sortOrder = this.sortOrder
    }
    this.backendService.getReminders(this.currGroup.id, sortBy, sortOrder).toPromise().then((data: any) => {
      this.reminders = data
    }).catch(() => {
      this.messageService.open("There was an issue getting the group's reminders.")
    })
  }

  deleteReminder(entry: ReminderModel) {
    this.backendService.deleteReminder(this.currGroup.id, entry.id).toPromise().then((data: any) => {
      this.messageService.open("Successfully deleted reminder.")
      this.reminders = data
    }).catch(() => {
      this.messageService.open("Unable to delete reminder. An error occured.")
    })
  }

}
