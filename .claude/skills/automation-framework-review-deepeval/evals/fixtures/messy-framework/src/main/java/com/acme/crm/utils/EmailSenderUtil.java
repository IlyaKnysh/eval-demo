package com.acme.crm.utils;

import java.util.Properties;
import javax.mail.Message;
import javax.mail.MessagingException;
import javax.mail.Session;
import javax.mail.Transport;
import javax.mail.internet.InternetAddress;
import javax.mail.internet.MimeMessage;

/**
 * Sends notification emails for test failures.
 */
public class EmailSenderUtil {

    public static void sendTestFailureNotification(String toAddress, String subject, String body) {
        Properties props = new Properties();
        props.put("mail.smtp.host", "smtp.acmecorp.internal");
        props.put("mail.smtp.port", "25");

        Session session = Session.getDefaultInstance(props);
        try {
            Message message = new MimeMessage(session);
            message.setFrom(new InternetAddress("qa-automation@acmecorp.com"));
            message.setRecipients(Message.RecipientType.TO, InternetAddress.parse(toAddress));
            message.setSubject(subject);
            message.setText(body);
            Transport.send(message);
        } catch (MessagingException e) {
            System.err.println("Failed to send notification email: " + e.getMessage());
        }
    }
}
