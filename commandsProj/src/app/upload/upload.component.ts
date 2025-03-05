import { Component, ViewEncapsulation, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../api.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule], // Ensure this is here for CommonModule
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css'],
  encapsulation: ViewEncapsulation.None,
})
export class UploadComponent {
  selectedFile: File | null = null;
  commands: string[] = [];
  imageUrl: string | null = null;

  constructor(private apiService: ApiService, private cdr: ChangeDetectorRef) {}

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
    
    if (this.selectedFile) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.imageUrl = e.target.result;
        this.cdr.detectChanges();  // Ensure change detection is triggered
      };
      reader.readAsDataURL(this.selectedFile);
    }
  }

  async uploadImage() {
    if (this.selectedFile) {
      try {
        const response = await this.apiService.uploadImage(this.selectedFile);
        this.commands = response.commands;
      } catch (error) {
        console.error('Error processing image:', error);
      }
    }
  }
}
